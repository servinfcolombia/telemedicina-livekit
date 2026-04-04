'use client'

import { useSession } from 'next-auth/react'
import { useRouter, useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import { VideoRoom } from '@/components/video/VideoRoom'

export default function RoomPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const params = useParams()
  const roomName = params.roomName as string

  const [userName, setUserName] = useState('')
  const [userIdentity, setUserIdentity] = useState('')
  const [joined, setJoined] = useState(false)

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin')
    }
  }, [status, router])

  if (status === 'loading') {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!joined) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100">
        <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-gray-900">Unirse a la Videoconsulta</h1>
            <p className="text-gray-600 mt-2">Sala: {roomName}</p>
          </div>

          <div className="space-y-6">
            <div>
              <label htmlFor="userName" className="block text-sm font-medium text-gray-700 mb-1">
                Tu nombre
              </label>
              <input
                id="userName"
                type="text"
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white text-gray-900"
                placeholder="Dr. Juan Perez"
                required
                style={{ backgroundColor: 'white', color: 'black' }}
              />
            </div>

            <div>
              <label htmlFor="userIdentity" className="block text-sm font-medium text-gray-700 mb-1">
                Tu identidad
              </label>
              <input
                id="userIdentity"
                type="text"
                value={userIdentity}
                onChange={(e) => setUserIdentity(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white text-gray-900"
                placeholder="doctor_001"
                required
                style={{ backgroundColor: 'white', color: 'black' }}
              />
            </div>

            <button
              onClick={() => {
                console.log('Join button clicked, userName:', userName, 'userIdentity:', userIdentity)
                if (userName && userIdentity) {
                  setJoined(true)
                } else {
                  alert('Por favor completa todos los campos')
                }
              }}
              className="w-full bg-primary-600 text-white py-3 rounded-lg font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            >
              Unirse a la consulta
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <VideoRoom
      roomName={roomName}
      userName={userName}
      userIdentity={userIdentity}
      accessToken={(session as any)?.accessToken}
      onLeave={() => router.push('/consultations')}
    />
  )
}
