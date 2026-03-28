'use client'

import { useEffect, useRef, useState } from 'react'
import {
  Room,
  Participant,
  VideoPresets,
  ConnectionQuality,
} from 'livekit-client'
import { useLiveKit } from '@/hooks/useLiveKit'
import { ParticipantTile } from './ParticipantTile'
import { VideoControls } from './Controls'

interface VideoRoomProps {
  roomName: string
  userName: string
  userIdentity: string
  onLeave?: () => void
}

export function VideoRoom({ roomName, userName, userIdentity, onLeave }: VideoRoomProps) {
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [showChat, setShowChat] = useState(false)
  const [connectionQuality, setConnectionQuality] = useState<ConnectionQuality>(ConnectionQuality.Good)
  const videoRef = useRef<HTMLDivElement>(null)

  const {
    room,
    connectionState,
    participants,
    isVideoEnabled,
    isAudioEnabled,
    isConnecting,
    error,
    connect,
    disconnect,
    toggleVideo,
    toggleAudio,
  } = useLiveKit({
    roomName,
    userName,
    userIdentity,
  })

  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [])

  const handleLeave = () => {
    disconnect()
    onLeave?.()
  }

  if (isConnecting) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p className="text-white">Conectando a la sala...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-center max-w-md">
          <div className="text-red-500 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <p className="text-white text-lg mb-4">Error de conexión</p>
          <p className="text-gray-400 mb-6">{error.message}</p>
          <button onClick={connect} className="btn-primary">
            Reintentar
          </button>
        </div>
      </div>
    )
  }

  const localParticipant = participants.find((p) => p.isLocal)
  const remoteParticipants = participants.filter((p) => !p.isLocal)

  return (
    <div className="flex flex-col h-screen bg-gray-900">
      <div className="flex-1 relative" ref={videoRef}>
        <div className="grid gap-2 p-2 h-full" style={{ 
          gridTemplateColumns: remoteParticipants.length > 0 ? '1fr 1fr' : '1fr',
          gridTemplateRows: remoteParticipants.length > 2 ? '1fr 1fr' : '1fr'
        }}>
          {localParticipant && (
            <ParticipantTile
              participant={localParticipant}
              isLocal={true}
              isVideoEnabled={isVideoEnabled}
              isAudioEnabled={isAudioEnabled}
              isFullscreen={isFullscreen}
              onFullscreen={() => setIsFullscreen(!isFullscreen)}
            />
          )}
          
          {remoteParticipants.map((participant) => (
            <ParticipantTile
              key={participant.identity}
              participant={participant}
              isLocal={false}
              isVideoEnabled={true}
              isAudioEnabled={true}
              isFullscreen={false}
            />
          ))}
        </div>

        <div className="absolute top-4 right-4 flex items-center space-x-2">
          <div className={`px-3 py-1 rounded-full text-sm ${
            connectionQuality === ConnectionQuality.Good ? 'bg-green-500' :
            connectionQuality === ConnectionQuality.Moderate ? 'bg-yellow-500' :
            'bg-red-500'
          } text-white`}>
            {connectionQuality === ConnectionQuality.Good ? 'Buena' :
             connectionQuality === ConnectionQuality.Moderate ? 'Regular' : 'Poor'}
          </div>
        </div>
      </div>

      <VideoControls
        isVideoEnabled={isVideoEnabled}
        isAudioEnabled={isAudioEnabled}
        onToggleVideo={toggleVideo}
        onToggleAudio={toggleAudio}
        onLeave={handleLeave}
        onShowChat={() => setShowChat(!showChat)}
        connectionState={connectionState}
      />
    </div>
  )
}
