'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  Room,
  RoomEvent,
  ConnectionState,
  LocalParticipant,
  RemoteParticipant,
  LocalVideoTrack,
  LocalAudioTrack,
} from 'livekit-client'

interface UseLiveKitOptions {
  roomName: string
  userName: string
  userIdentity: string
}

interface UseLiveKitReturn {
  room: Room | null
  connectionState: ConnectionState
  participants: (LocalParticipant | RemoteParticipant)[]
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
  const [participants, setParticipants] = useState<(LocalParticipant | RemoteParticipant)[]>([])
  const [localParticipant, setLocalParticipant] = useState<LocalParticipant | null>(null)
  const [isVideoEnabled, setIsVideoEnabled] = useState(false)
  const [isAudioEnabled, setIsAudioEnabled] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const connect = useCallback(async () => {
    if (!roomName || isConnecting) return

    setIsConnecting(true)
    setError(null)

    try {
      const tokenResponse = await fetch('/api/livekit/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ roomName, userName, userIdentity }),
      })

      if (!tokenResponse.ok) {
        throw new Error('Failed to get LiveKit token')
      }

      const { token } = await tokenResponse.json()

      const newRoom = new Room({
        adaptiveStream: true,
        dynacast: true,
        videoCaptureDefaults: {
          resolution: { width: 1280, height: 720 },
        },
      })

      newRoom.on(RoomEvent.ConnectionStateChanged, (state) => {
        setConnectionState(state)
      })

      newRoom.on(RoomEvent.ParticipantConnected, () => {
        setParticipants([...newRoom.participants.values()])
      })

      newRoom.on(RoomEvent.ParticipantDisconnected, () => {
        setParticipants([...newRoom.participants.values()])
      })

      await newRoom.connect(
        process.env.NEXT_PUBLIC_LIVEKIT_URL || 'ws://localhost:7880',
        token
      )

      setRoom(newRoom)
      setLocalParticipant(newRoom.localParticipant)
      setParticipants([newRoom.localParticipant, ...newRoom.participants.values()])

      const videoTracks = newRoom.localParticipant.videoTracks
      const audioTracks = newRoom.localParticipant.audioTracks

      setIsVideoEnabled(videoTracks.size > 0)
      setIsAudioEnabled(audioTracks.size > 0)
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
      if (isVideoEnabled) {
        localParticipant.videoTracks.forEach((publication) => {
          if (publication.track) {
            publication.track.stop()
          }
        })
      } else {
        localParticipant.setCameraEnabled(true)
      }
      setIsVideoEnabled(!isVideoEnabled)
    }
  }, [localParticipant, isVideoEnabled])

  const toggleAudio = useCallback(() => {
    if (localParticipant) {
      if (isAudioEnabled) {
        localParticipant.audioTracks.forEach((publication) => {
          if (publication.track) {
            publication.track.stop()
          }
        })
      } else {
        localParticipant.setMicrophoneEnabled(true)
      }
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
