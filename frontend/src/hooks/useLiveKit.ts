'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  Room,
  RoomEvent,
  ConnectionState,
  LocalParticipant,
  RemoteParticipant,
} from 'livekit-client'

interface UseLiveKitOptions {
  roomName: string
  userName: string
  userIdentity: string
}

interface UseLiveKitReturn {
  room: Room | null
  connectionState: ConnectionState
  participants: RemoteParticipant[]
  localParticipant: LocalParticipant | null
  isVideoEnabled: boolean
  isAudioEnabled: boolean
  isConnecting: boolean
  error: Error | null
  connect: () => Promise<void>
  disconnect: () => void
  toggleVideo: () => void
  toggleAudio: () => void
}

export function useLiveKit({
  roomName,
  userName,
  userIdentity,
}: UseLiveKitOptions): UseLiveKitReturn {
  const [room, setRoom] = useState<Room | null>(null)
  const [connectionState, setConnectionState] = useState<ConnectionState>(ConnectionState.Disconnected)
  const [participants, setParticipants] = useState<RemoteParticipant[]>([])
  const [localParticipant, setLocalParticipant] = useState<LocalParticipant | null>(null)
  const [isVideoEnabled, setIsVideoEnabled] = useState(false)
  const [isAudioEnabled, setIsAudioEnabled] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const connect = useCallback(async () => {
    if (!roomName || isConnecting) {
      console.log('useLiveKit: not connecting, roomName:', roomName, 'isConnecting:', isConnecting)
      return
    }

    setIsConnecting(true)
    setError(null)

    console.log('useLiveKit: connecting to room:', roomName)

    try {
      const tokenResponse = await fetch('/api/livekit/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ roomName, userName, userIdentity }),
      })

      console.log('useLiveKit: token response status:', tokenResponse.status)

      if (!tokenResponse.ok) {
        const errorText = await tokenResponse.text()
        console.error('useLiveKit: token error:', errorText)
        throw new Error('Failed to get LiveKit token: ' + errorText)
      }

      const { token } = await tokenResponse.json()
      console.log('useLiveKit: got token:', token.substring(0, 30) + '...')

      const newRoom = new Room({
        adaptiveStream: true,
        dynacast: true,
        videoCaptureDefaults: {
          resolution: { width: 1280, height: 720 },
        },
      }) as any

      newRoom.on(RoomEvent.ConnectionStateChanged, (state: any) => {
        console.log('Connection state:', state)
        setConnectionState(state)
      })

      newRoom.on(RoomEvent.ParticipantConnected, () => {
        setParticipants([])
      })

      newRoom.on(RoomEvent.ParticipantDisconnected, () => {
        setParticipants([])
      })

      console.log('Connecting to:', process.env.NEXT_PUBLIC_LIVEKIT_URL || 'ws://localhost:7880')
      console.log('Token (first 50 chars):', token.substring(0, 50))

      // Get ICE servers
      let iceServers = []
      try {
        const iceResponse = await fetch('/api/livekit/ice-servers')
        if (iceResponse.ok) {
          const iceData = await iceResponse.json()
          iceServers = iceData.iceServers || []
          console.log('ICE servers:', iceServers)
        }
      } catch (iceErr) {
        console.warn('Could not fetch ICE servers, using defaults:', iceErr)
        iceServers = [
          { urls: 'stun:stun.l.google.com:19302' },
          { urls: 'turn:localhost:3478', username: 'devkey', credential: 'mysecret123' },
        ]
      }

      try {
        await newRoom.connect(
          process.env.NEXT_PUBLIC_LIVEKIT_URL || 'ws://localhost:7880',
          token,
          { 
            autoSubscribe: true,
            iceServers: iceServers,
          } as any
        )
        console.log('Connected successfully!')
      } catch (connectErr) {
        console.error('Connection error:', connectErr)
        throw connectErr
      }

      setRoom(newRoom)
      setLocalParticipant(newRoom.localParticipant)
      setParticipants([])

      setIsVideoEnabled(true)
      setIsAudioEnabled(true)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Connection failed'))
    } finally {
      setIsConnecting(false)
    }
  }, [roomName, userName, userIdentity, isConnecting])

  const disconnect = useCallback(() => {
    if (room) {
      room.disconnect()
      setRoom(null)
      setLocalParticipant(null)
      setParticipants([])
      setConnectionState(ConnectionState.Disconnected)
    }
  }, [room])

  const toggleVideo = useCallback(() => {
    if (localParticipant) {
      setIsVideoEnabled(!isVideoEnabled)
    }
  }, [localParticipant, isVideoEnabled])

  const toggleAudio = useCallback(() => {
    if (localParticipant) {
      setIsAudioEnabled(!isAudioEnabled)
    }
  }, [localParticipant, isAudioEnabled])

  useEffect(() => {
    return () => {
      if (room) {
        room.disconnect()
      }
    }
  }, [room])

  return {
    room,
    connectionState,
    participants,
    localParticipant,
    isVideoEnabled,
    isAudioEnabled,
    isConnecting,
    error,
    connect,
    disconnect,
    toggleVideo,
    toggleAudio,
  }
}
