'use client'

import { useEffect, useRef } from 'react'
import {
  Participant,
  VideoTrack,
  AudioTrack,
  Track,
} from 'livekit-client'

interface ParticipantTileProps {
  participant: Participant
  isLocal: boolean
  isVideoEnabled: boolean
  isAudioEnabled: boolean
  isFullscreen: boolean
  onFullscreen?: () => void
}

export function ParticipantTile({
  participant,
  isLocal,
  isVideoEnabled,
  isAudioEnabled,
  isFullscreen,
  onFullscreen,
}: ParticipantTileProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const audioRef = useRef<HTMLAudioElement>(null)

  const getConnectionQualityColor = (_quality: unknown) => {
    return 'bg-green-500'
  }

  return (
    <div 
      className={`relative bg-gray-800 rounded-lg overflow-hidden ${
        isFullscreen ? 'fixed inset-0 z-50' : 'aspect-video'
      }`}
    >
      {isVideoEnabled ? (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted={isLocal}
          className="w-full h-full object-cover"
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center bg-gray-700">
          <div className="w-24 h-24 rounded-full bg-gray-600 flex items-center justify-center">
            <span className="text-3xl font-bold text-white">
              {participant.name?.charAt(0) || participant.identity.charAt(0).toUpperCase()}
            </span>
          </div>
        </div>
      )}

      <audio ref={audioRef} autoPlay muted={isLocal} />

      <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="bg-black/50 backdrop-blur-sm px-3 py-1 rounded-full">
            <span className="text-white text-sm">
              {participant.name || participant.identity}
              {isLocal && ' (Tú)'}
            </span>
          </div>
          
          {!isAudioEnabled && (
            <div className="bg-red-500 p-1 rounded-full" title="Micrófono silenciado">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
              </svg>
            </div>
          )}
        </div>

        <button
          onClick={onFullscreen}
          className="bg-black/50 backdrop-blur-sm p-1 rounded-full hover:bg-black/70 transition-colors"
          aria-label={isFullscreen ? 'Salir de pantalla completa' : 'Pantalla completa'}
        >
          {isFullscreen ? (
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          )}
        </button>
      </div>

      <div className="absolute top-2 right-2">
        <div className="w-3 h-3 rounded-full bg-green-500" />
      </div>
    </div>
  )
}
