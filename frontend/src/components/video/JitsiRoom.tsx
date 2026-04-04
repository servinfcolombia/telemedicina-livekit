'use client'

import { useState, useCallback } from 'react'

interface JitsiRoomProps {
  roomName: string
  userName: string
  userIdentity: string
  onLeave?: () => void
}

export function JitsiRoom({ roomName, userName, userIdentity, onLeave }: JitsiRoomProps) {
  const [opened, setOpened] = useState(false)

  const jitsiUrl = `https://meet.jit.si/telemedicina-${roomName}`

  const openJitsi = useCallback(() => {
    window.open(jitsiUrl, '_blank')
    setOpened(true)
  }, [jitsiUrl])

  const handleLeave = useCallback(() => {
    onLeave?.()
  }, [onLeave])

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-900">
      <div className="text-center max-w-md p-8">
        <div className="text-blue-500 mb-4">
          <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        </div>
        <p className="text-white text-lg mb-2">Videoconsulta</p>
        <p className="text-gray-400 mb-6">
          Se abrirá una nueva pestaña con la sala de videoconsulta. Ingresa tu nombre cuando se te solicite.
        </p>
        <div className="space-y-3">
          <button
            onClick={openJitsi}
            className="w-full px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium"
          >
            {opened ? 'Abrir nuevamente' : 'Iniciar videoconsulta'}
          </button>
          <button
            onClick={handleLeave}
            className="w-full px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium"
          >
            Volver
          </button>
        </div>
      </div>
    </div>
  )
}
