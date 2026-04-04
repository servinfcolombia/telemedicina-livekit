'use client'

import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

const PACIENTES_EJEMPLO = [
  { id: 'patient_175525', nombre: 'Carlos Garcia' },
  { id: 'patient_175526', nombre: 'Maria Lopez' },
  { id: 'patient_175527', nombre: 'Juan Perez' },
]

export default function NewConsultationPage() {
  const { data: session, status, update: updateSession } = useSession()
  const router = useRouter()
  const [patientId, setPatientId] = useState('')
  const [scheduledAt, setScheduledAt] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  console.log('Session on new consultation page:', session)
  console.log('Status:', status)

  useEffect(() => {
    if (!session && status === 'unauthenticated') {
      router.push('/auth/signin')
    }
  }, [session, status, router])

  // Refresh session when page loads
  useEffect(() => {
    if (status === 'authenticated' && !session?.accessToken) {
      console.log('Refreshing session...')
      updateSession()
    }
  }, [status, session, updateSession])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    if (!patientId || !scheduledAt) {
      setError('Por favor completa todos los campos')
      setLoading(false)
      return
    }

    try {
      let token: string | undefined = undefined
      
      if (session?.accessToken) {
        token = session.accessToken
      } else if ((session as any)?.user?.accessToken) {
        token = (session as any).user.accessToken
      } else if ((session as any)?.token) {
        token = (session as any).token
      }
      
      console.log('Token disponible:', !!token)
      console.log('API URL:', process.env.NEXT_PUBLIC_API_URL)
      
      if (!token) {
        setError('Tu sesión expiró. Por favor cierra sesión y vuelve a iniciar.')
        setLoading(false)
        return
      }
      
      const body = {
        patient_id: patientId,
        scheduled_at: new Date(scheduledAt).toISOString(),
        duration_minutes: 30,
      }
      console.log('Enviando:', body)
      
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/consultations/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      })

      console.log('Response status:', res.status)
      
      if (res.ok) {
        router.push('/consultations')
      } else {
        const text = await res.text()
        console.log('Response error:', text)
        setError(`Error del servidor: ${res.status}`)
      }
    } catch (err: any) {
      console.error('Error:', err)
      setError('Error de conexión: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  if (!session) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>Debes iniciar sesión primero</p>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="max-w-md mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Nueva Consulta</h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm border border-red-200">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="patientId" className="block text-sm font-medium text-gray-700 mb-1">
              Paciente
            </label>
            <select
              id="patientId"
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900"
              required
              style={{ backgroundColor: 'white', color: 'black' }}
            >
              <option value="">Selecciona un paciente</option>
              {PACIENTES_EJEMPLO.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nombre} ({p.id})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="scheduledAt" className="block text-sm font-medium text-gray-700 mb-1">
              Fecha y Hora
            </label>
            <input
              id="scheduledAt"
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900"
              required
              style={{ backgroundColor: 'white', color: 'black' }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary-600 text-white py-3 rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50"
          >
            {loading ? 'Creando...' : 'Crear Consulta'}
          </button>

          <button
            type="button"
            onClick={() => router.push('/consultations')}
            className="w-full bg-gray-200 text-gray-700 py-3 rounded-lg font-medium hover:bg-gray-300"
          >
            Cancelar
          </button>
        </form>
      </div>
    </div>
  )
}
