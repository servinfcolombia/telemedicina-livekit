'use client'

import { useEffect, useRef, useCallback, useState } from 'react'

declare global {
  interface Window {
    JitsiMeetExternalAPI: any
  }
}

interface UseJitsiOptions {
  roomName: string
  userName: string
  containerId: string
}

interface UseJitsiReturn {
  isConnected: boolean
  isConnecting: boolean
  error: Error | null
  isVideoEnabled: boolean
  isAudioEnabled: boolean
  toggleVideo: () => void
  toggleAudio: () => void
  disconnect: () => void
}

let scriptLoaded = false
let scriptLoading = false

function loadJitsiScript(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (scriptLoaded && window.JitsiMeetExternalAPI) {
      resolve()
      return
    }

    if (scriptLoading) {
      const checkInterval = setInterval(() => {
        if (window.JitsiMeetExternalAPI) {
          scriptLoaded = true
          clearInterval(checkInterval)
          resolve()
        }
      }, 100)
      setTimeout(() => {
        clearInterval(checkInterval)
        reject(new Error('Timeout loading Jitsi script'))
      }, 15000)
      return
    }

    scriptLoading = true

    const script = document.createElement('script')
    script.src = 'https://meet.jit.si/external_api.js'
    script.async = true
    script.crossOrigin = 'anonymous'

    const timeout = setTimeout(() => {
      script.onerror?.(new Event('timeout'))
    }, 15000)

    script.onload = () => {
      clearTimeout(timeout)
      scriptLoaded = true
      scriptLoading = false
      console.log('Jitsi script loaded successfully')
      resolve()
    }

    script.onerror = (e) => {
      clearTimeout(timeout)
      scriptLoading = false
      console.error('Failed to load Jitsi script, error:', e)
      reject(new Error('No se pudo cargar el script de Jitsi. Verifica tu conexión a internet.'))
    }

    document.head.appendChild(script)
  })
}

export function useJitsi({ roomName, userName, containerId }: UseJitsiOptions): UseJitsiReturn {
  const apiRef = useRef<any>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [isVideoEnabled, setIsVideoEnabled] = useState(true)
  const [isAudioEnabled, setIsAudioEnabled] = useState(true)

  const disconnect = useCallback(() => {
    if (apiRef.current) {
      try {
        apiRef.current.dispose()
      } catch (e) {
        console.warn('Error disposing Jitsi API:', e)
      }
      apiRef.current = null
      setIsConnected(false)
    }
  }, [])

  const toggleVideo = useCallback(() => {
    if (apiRef.current) {
      apiRef.current.executeCommand('toggleVideo')
      setIsVideoEnabled(prev => !prev)
    }
  }, [])

  const toggleAudio = useCallback(() => {
    if (apiRef.current) {
      apiRef.current.executeCommand('toggleAudio')
      setIsAudioEnabled(prev => !prev)
    }
  }, [])

  useEffect(() => {
    if (!roomName || !userName) return

    let cancelled = false

    const initJitsi = async () => {
      setIsConnecting(true)
      setError(null)

      try {
        await loadJitsiScript()

        if (cancelled) return

        if (!window.JitsiMeetExternalAPI) {
          throw new Error('Jitsi API no disponible después de cargar el script')
        }

        let container: HTMLElement | null = null
        let retries = 0
        const maxRetries = 20

        while (!container && retries < maxRetries) {
          container = document.getElementById(containerId)
          if (!container) {
            await new Promise(resolve => setTimeout(resolve, 200))
            retries++
          }
        }

        if (!container) {
          throw new Error(`Contenedor #${containerId} no encontrado después de ${maxRetries * 200}ms`)
        }

        console.log('Creando conferencia Jitsi:', `telemedicina-${roomName}`)

        const api = new window.JitsiMeetExternalAPI('meet.jit.si', {
          roomName: `telemedicina-${roomName}`,
          width: '100%',
          height: '100%',
          parentNode: container,
          userInfo: {
            displayName: userName,
          },
          configOverwrite: {
            startWithAudioMuted: false,
            startWithVideoMuted: false,
            prejoinPageEnabled: false,
            disableDeepLinking: true,
          },
          interfaceConfigOverwrite: {
            SHOW_JITSI_WATERMARK: false,
            SHOW_WATERMARK_FOR_GUESTS: false,
            DEFAULT_BACKGROUND: '#1a1a1a',
            TOOLBAR_BUTTONS: [
              'microphone',
              'camera',
              'desktop',
              'fullscreen',
              'floating',
              'hangup',
              'chat',
              'settings',
              'tileview',
            ],
          },
        })

        if (cancelled) {
          api.dispose()
          return
        }

        apiRef.current = api

        api.addListener('videoConferenceJoined', () => {
          console.log('Jitsi: Conferencia unida')
          if (!cancelled) {
            setIsConnected(true)
            setIsConnecting(false)
          }
        })

        api.addListener('videoConferenceLeft', () => {
          console.log('Jitsi: Conferencia abandonada')
          if (!cancelled) {
            setIsConnected(false)
          }
        })

        api.addListener('participantJoined', (participant: any) => {
          console.log('Jitsi: Participante unido:', participant?.displayName)
        })

        api.addListener('participantLeft', (participant: any) => {
          console.log('Jitsi: Participante abandonó:', participant?.displayName)
        })

        api.addListener('errorOccurred', (event: any) => {
          console.error('Jitsi error:', event)
          if (!cancelled) {
            setError(new Error(event.message || 'Error en Jitsi'))
          }
        })

      } catch (err) {
        console.error('Error inicializando Jitsi:', err)
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error('Error de conexión'))
          setIsConnecting(false)
        }
      }
    }

    initJitsi()

    return () => {
      cancelled = true
      disconnect()
    }
  }, [roomName, userName, containerId, disconnect])

  return {
    isConnected,
    isConnecting,
    error,
    isVideoEnabled,
    isAudioEnabled,
    toggleVideo,
    toggleAudio,
    disconnect,
  }
}
