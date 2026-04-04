'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import Peer, { MediaConnection } from 'peerjs'
import { VideoControls } from './Controls'

interface VideoRoomProps {
  roomName: string
  userName: string
  userIdentity: string
  accessToken?: string
  onLeave?: () => void
}

export function VideoRoom({ roomName, userName, userIdentity, accessToken, onLeave }: VideoRoomProps) {
  const peerRef = useRef<Peer | null>(null)
  const localVideoRef = useRef<HTMLVideoElement>(null)
  const localStreamRef = useRef<MediaStream | null>(null)
  const callsRef = useRef<MediaConnection[]>([])
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const recordingStartTimeRef = useRef<Date | null>(null)
  const recognitionRef = useRef<any>(null)
  
  const [remoteVideos, setRemoteVideos] = useState<Map<string, MediaStream>>(new Map())
  const [isVideoEnabled, setIsVideoEnabled] = useState(true)
  const [isAudioEnabled, setIsAudioEnabled] = useState(true)
  const [isConnected, setIsConnected] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isRecording, setIsRecording] = useState(false)
  const [recordingDuration, setRecordingDuration] = useState(0)
  const [transcript, setTranscript] = useState('')
  const [isTranscribing, setIsTranscribing] = useState(false)
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null)
  const transcriptRef = useRef('')

  const startRecording = useCallback((stream: MediaStream) => {
    try {
      const audioTracks = stream.getAudioTracks()
      if (audioTracks.length === 0) {
        console.warn('No hay tracks de audio para grabar')
        return
      }

      const audioStream = new MediaStream(audioTracks)
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/ogg'

      const recorder = new MediaRecorder(audioStream, { mimeType })
      audioChunksRef.current = []
      recordingStartTimeRef.current = new Date()

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType })
        console.log(`Grabación finalizada: ${audioBlob.size} bytes`)
        await uploadRecording(audioBlob)
      }

      recorder.start(1000)
      mediaRecorderRef.current = recorder
      setIsRecording(true)
      setRecordingDuration(0)

      recordingTimerRef.current = setInterval(() => {
        setRecordingDuration(prev => prev + 1)
      }, 1000)

      console.log('Grabación de audio iniciada')
    } catch (err) {
      console.error('Error al iniciar grabación:', err)
    }
  }, [])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current)
      }
    }
  }, [])

  const startTranscription = useCallback(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) {
      console.warn('Speech Recognition no soportado en este navegador')
      return
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'es-ES'

    recognition.onresult = (event: any) => {
      let finalTranscript = ''
      let interimTranscript = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const t = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalTranscript += t + ' '
        } else {
          interimTranscript += t
        }
      }

      if (finalTranscript) {
        transcriptRef.current += finalTranscript
        setTranscript(transcriptRef.current)
      }
    }

    recognition.onerror = (event: any) => {
      console.log('Speech recognition error:', event.error)
      if (event.error !== 'no-speech') {
        setTimeout(() => {
          try {
            recognition.start()
          } catch (e) {}
        }, 1000)
      }
    }

    recognition.onend = () => {
      try {
        recognition.start()
      } catch (e) {}
    }

    try {
      recognition.start()
      recognitionRef.current = recognition
      setIsTranscribing(true)
      transcriptRef.current = ''
      setTranscript('')
      console.log('Transcripción en tiempo real iniciada')
    } catch (e) {
      console.error('Error iniciando transcripción:', e)
    }
  }, [])

  const stopTranscription = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
      recognitionRef.current = null
      setIsTranscribing(false)
    }
  }, [])

  const uploadRecording = async (audioBlob: Blob) => {
    if (!accessToken || !recordingStartTimeRef.current) return

    try {
      const consultationId = roomName.replace('room_', '')
      const formData = new FormData()
      formData.append('file', audioBlob, `consulta_${consultationId}.webm`)
      formData.append('consultation_id', consultationId)
      formData.append('started_at', recordingStartTimeRef.current.toISOString())
      formData.append('duration_seconds', String(recordingDuration))

      if (transcriptRef.current.trim()) {
        formData.append('transcription', transcriptRef.current.trim())
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/recordings/`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        body: formData,
      })

      if (response.ok) {
        console.log('Grabación guardada exitosamente')
      } else {
        console.error('Error al guardar grabación:', await response.text())
      }
    } catch (err) {
      console.error('Error subiendo grabación:', err)
    }
  }

  const addRemoteAudioToRecording = useCallback((remoteStream: MediaStream) => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      const audioTracks = remoteStream.getAudioTracks()
      if (audioTracks.length > 0) {
        const currentStream = mediaRecorderRef.current.stream
        audioTracks.forEach(track => {
          if (!currentStream.getAudioTracks().find(t => t.id === track.id)) {
            currentStream.addTrack(track)
          }
        })
      }
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    const init = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: true,
        })

        if (cancelled) {
          stream.getTracks().forEach(t => t.stop())
          return
        }

        localStreamRef.current = stream
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = stream
        }

        const peerId = `telemedicina-${roomName}-${userIdentity}-${Date.now()}`
        const roomKey = `telemedicina-${roomName}`

        const peer = new Peer(peerId, {
          debug: 0,
        })

        peerRef.current = peer

        peer.on('open', () => {
          if (!cancelled) {
            console.log('Conectado como:', peerId)
            setIsConnected(true)
            setLoading(false)

            startRecording(stream)
            startTranscription()
          }
        })

        peer.on('call', (call: MediaConnection) => {
          console.log('Llamada entrante de:', call.peer)
          call.answer(stream)
          callsRef.current.push(call)

          call.on('stream', (remoteStream) => {
            if (!cancelled) {
              const callerId = call.peer
              console.log('Stream remoto recibido de:', callerId)
              addRemoteAudioToRecording(remoteStream)
              setRemoteVideos(prev => {
                const next = new Map(prev)
                next.set(callerId, remoteStream)
                return next
              })
            }
          })

          call.on('close', () => {
            setRemoteVideos(prev => {
              const next = new Map(prev)
              next.delete(call.peer)
              return next
            })
          })
        })

        peer.on('error', (err) => {
          console.error('Peer error:', err.type, err.message)
        })

        const discoverAndConnect = () => {
          try {
            const existingPeersStr = localStorage.getItem(`peers_${roomKey}`)
            if (existingPeersStr) {
              const existingPeers: string[] = JSON.parse(existingPeersStr)
              for (const existingPeerId of existingPeers) {
                if (existingPeerId !== peerId && peer) {
                  console.log('Intentando conectar a:', existingPeerId)
                  try {
                    const call = peer.call(existingPeerId, stream)
                    if (call) {
                      callsRef.current.push(call)
                      call.on('stream', (remoteStream) => {
                        if (!cancelled) {
                          addRemoteAudioToRecording(remoteStream)
                          setRemoteVideos(prev => {
                            const next = new Map(prev)
                            next.set(existingPeerId, remoteStream)
                            return next
                          })
                        }
                      })
                    }
                  } catch (e) {
                    console.log('No se pudo conectar a:', existingPeerId)
                  }
                }
              }
            }

            const existingPeers: string[] = existingPeersStr ? JSON.parse(existingPeersStr) : []
            if (!existingPeers.includes(peerId)) {
              existingPeers.push(peerId)
              localStorage.setItem(`peers_${roomKey}`, JSON.stringify(existingPeers))
            }
          } catch (e) {
            console.log('Discovery error:', e)
          }
        }

        discoverAndConnect()
        const interval = setInterval(discoverAndConnect, 3000)

        if (!cancelled) {
          // @ts-ignore
          window._peerCleanup = () => {
            clearInterval(interval)
            try {
              const existingPeersStr = localStorage.getItem(`peers_${roomKey}`)
              if (existingPeersStr) {
                const existingPeers: string[] = JSON.parse(existingPeersStr)
                const filtered = existingPeers.filter(p => p !== peerId)
                localStorage.setItem(`peers_${roomKey}`, JSON.stringify(filtered))
              }
            } catch (e) {}
          }
        }

      } catch (err: any) {
        console.error('Error:', err)
        if (!cancelled) {
          setError(err.message || 'No se pudo acceder a la cámara')
          setLoading(false)
        }
      }
    }

    init()

    return () => {
      cancelled = true
      stopRecording()
      stopTranscription()
      // @ts-ignore
      if (window._peerCleanup) {
        // @ts-ignore
        window._peerCleanup()
      }
      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach(t => t.stop())
      }
      if (peerRef.current) {
        peerRef.current.destroy()
      }
      callsRef.current.forEach(c => c.close())
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current)
      }
    }
  }, [roomName, userIdentity, startRecording, stopRecording, stopTranscription, startTranscription, addRemoteAudioToRecording])

  const toggleVideo = useCallback(() => {
    if (localStreamRef.current) {
      localStreamRef.current.getVideoTracks().forEach(t => {
        t.enabled = !t.enabled
      })
      setIsVideoEnabled(prev => !prev)
    }
  }, [])

  const toggleAudio = useCallback(() => {
    if (localStreamRef.current) {
      localStreamRef.current.getAudioTracks().forEach(t => {
        t.enabled = !t.enabled
      })
      setIsAudioEnabled(prev => !prev)
    }
  }, [])

  const handleLeave = useCallback(() => {
    stopRecording()
    stopTranscription()
    // @ts-ignore
    if (window._peerCleanup) {
      // @ts-ignore
      window._peerCleanup()
    }
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(t => t.stop())
    }
    if (peerRef.current) {
      peerRef.current.destroy()
    }
    onLeave?.()
  }, [onLeave, stopRecording, stopTranscription])

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-center max-w-md p-8">
          <div className="text-red-500 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <p className="text-white text-lg mb-4">Error</p>
          <p className="text-gray-400 mb-6">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium"
          >
            Reintentar
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen bg-gray-900 relative">
      <div className="flex-1 grid gap-2 p-2 overflow-auto"
        style={{
          gridTemplateColumns: remoteVideos.size > 0 ? 'repeat(auto-fit, minmax(300px, 1fr))' : '1fr',
        }}>
        <div className="relative bg-gray-800 rounded-lg overflow-hidden aspect-video">
          <video
            ref={localVideoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
          />
          <div className="absolute bottom-2 left-2 bg-black/50 px-2 py-1 rounded text-white text-sm">
            {userName} (Tú)
          </div>
        </div>

        {Array.from(remoteVideos.entries()).map(([peerId, stream]) => (
          <RemoteVideoTile key={peerId} peerId={peerId} stream={stream} />
        ))}
      </div>

      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900 z-50">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
            <p className="text-white">Conectando a la videoconsulta...</p>
            <p className="text-gray-400 text-sm mt-2">Esperando participantes</p>
          </div>
        </div>
      )}

      {!loading && (
        <div className="absolute top-4 right-4 z-10 flex items-center space-x-2">
          {isTranscribing && (
            <div className="bg-blue-600 px-3 py-1 rounded-full text-sm text-white flex items-center">
              <span className="w-2 h-2 bg-white rounded-full mr-2 animate-pulse"></span>
              Transcribiendo
            </div>
          )}
          {isRecording && (
            <div className="bg-red-600 px-3 py-1 rounded-full text-sm text-white flex items-center">
              <span className="w-2 h-2 bg-white rounded-full mr-2 animate-pulse"></span>
              Grabando {formatDuration(recordingDuration)}
            </div>
          )}
          <div className="bg-green-500 px-3 py-1 rounded-full text-sm text-white">
            Conectado - {remoteVideos.size + 1} participante(s)
          </div>
        </div>
      )}

      {transcript && (
        <div className="absolute bottom-20 left-4 right-4 z-10 bg-black/70 rounded-lg p-3 max-h-32 overflow-y-auto">
          <p className="text-white text-sm">{transcript}</p>
        </div>
      )}

      <div className="absolute bottom-0 left-0 right-0 z-10">
        <VideoControls
          isVideoEnabled={isVideoEnabled}
          isAudioEnabled={isAudioEnabled}
          onToggleVideo={toggleVideo}
          onToggleAudio={toggleAudio}
          onLeave={handleLeave}
          onShowChat={() => {}}
          connectionState={isConnected ? 'connected' : 'connecting'}
        />
      </div>
    </div>
  )
}

function RemoteVideoTile({ peerId, stream }: { peerId: string; stream: MediaStream }) {
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.srcObject = stream
    }
  }, [stream])

  const displayName = peerId.split('-').slice(0, -1).join('-').split('_').pop() || peerId

  return (
    <div className="relative bg-gray-800 rounded-lg overflow-hidden aspect-video">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        className="w-full h-full object-cover"
      />
      <div className="absolute bottom-2 left-2 bg-black/50 px-2 py-1 rounded text-white text-sm">
        {displayName}
      </div>
    </div>
  )
}
