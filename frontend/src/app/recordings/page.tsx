'use client'

import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { TrashIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline'

interface Recording {
  id: string
  consultation_id: string
  file_name: string
  file_size: number
  duration_seconds: number
  uploaded_at: string
  uploaded_by: string
}

export default function RecordingsPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [recordings, setRecordings] = useState<Recording[]>([])
  const [loading, setLoading] = useState(true)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin')
    }
  }, [status, router])

  useEffect(() => {
    if (session) {
      fetchAllRecordings()
    }
  }, [session])

  const fetchAllRecordings = async () => {
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/recordings/list-all`,
        {
          headers: {
            Authorization: `Bearer ${(session as any)?.accessToken}`,
          },
        }
      )
      if (res.ok) {
        const data = await res.json()
        setRecordings(data)
      } else {
        console.error('Error response:', await res.text())
      }
    } catch (error) {
      console.error('Error fetching recordings:', error)
    } finally {
      setLoading(false)
    }
  }

  const downloadRecording = (consultationId: string, fileName: string) => {
    window.open(
      `${process.env.NEXT_PUBLIC_API_URL}/api/v1/recordings/${consultationId}/${fileName}`,
      '_blank'
    )
  }

  const deleteRecording = async (recordingId: string) => {
    if (!confirm('¿Estás seguro de que deseas eliminar esta grabación?')) return
    
    setDeletingId(recordingId)
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/recordings/${recordingId}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${(session as any)?.accessToken}`,
          },
        }
      )
      if (res.ok) {
        setRecordings(recordings.filter(r => r.id !== recordingId))
      } else {
        console.error('Error deleting:', await res.text())
        alert('Error al eliminar la grabación')
      }
    } catch (error) {
      console.error('Error deleting recording:', error)
      alert('Error al eliminar la grabación')
    } finally {
      setDeletingId(null)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  if (status === 'loading' || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Grabaciones de Consultas</h1>
        <button
          onClick={() => router.push('/consultations')}
          className="btn-primary"
        >
          Volver a Consultas
        </button>
      </div>

      {recordings.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm p-8 text-center">
          <p className="text-gray-600">No hay grabaciones disponibles</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Consulta
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Archivo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tamaño
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Fecha
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {recordings.map((recording) => (
                <tr key={recording.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {recording.consultation_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {recording.file_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatFileSize(recording.file_size)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(recording.uploaded_at).toLocaleString('es-ES')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button
                      onClick={() => downloadRecording(recording.consultation_id, recording.file_name)}
                      className="text-primary-600 hover:text-primary-900 p-2"
                      title="Descargar"
                    >
                      <ArrowDownTrayIcon className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => deleteRecording(recording.id)}
                      disabled={deletingId === recording.id}
                      className="text-red-600 hover:text-red-900 p-2 disabled:opacity-50"
                      title="Eliminar"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
