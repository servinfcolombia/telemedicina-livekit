'use client'

import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

interface FhirEntity {
  code: string
  display: string
  text: string
  system: string
  dosage?: string
  value?: number
}

interface FhirData {
  consultation_id?: string
  transcription?: string
  fhir_entities?: {
    conditions: FhirEntity[]
    medications: FhirEntity[]
    observations: FhirEntity[]
    procedures: FhirEntity[]
  }
  entities?: {
    conditions: FhirEntity[]
    medications: FhirEntity[]
    observations: FhirEntity[]
    procedures: FhirEntity[]
  }
  fhir_bundle?: any
  fhir_valid?: boolean
  reviewed?: boolean
}

export default function FhirPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [consultationId, setConsultationId] = useState('')
  const [fhirData, setFhirData] = useState<FhirData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin')
    }
  }, [status, router])

  const fetchFhir = async () => {
    if (!consultationId.trim()) return
    setLoading(true)
    setError('')
    setFhirData(null)

    try {
      const token = (session as any)?.accessToken || (session as any)?.user?.accessToken
      console.log('FHIR page - session keys:', Object.keys(session || {}))
      console.log('FHIR page - token available:', !!token)

      if (!token) {
        setError('No hay token de autenticación. Cierra sesión y vuelve a iniciar.')
        setLoading(false)
        return
      }

      const url = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/ia/fhir/${consultationId}`
      console.log('FHIR fetch URL:', url)

      const res = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      console.log('FHIR response status:', res.status)

      if (!res.ok) {
        const errorText = await res.text()
        console.log('FHIR error response:', errorText)
        setError(`Error: ${res.status} - ${errorText}`)
        return
      }

      const data = await res.json()
      console.log('FHIR data received:', data)
      setFhirData(data)
    } catch (err: any) {
      console.error('FHIR fetch error:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const entities = fhirData?.entities || fhirData?.fhir_entities
  const totalEntities = entities
    ? (entities.conditions?.length || 0) +
      (entities.medications?.length || 0) +
      (entities.observations?.length || 0) +
      (entities.procedures?.length || 0)
    : 0

  if (status === 'loading') {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Entidades FHIR</h1>
        <button
          onClick={() => router.push('/transcriptions')}
          className="btn-primary"
        >
          Volver a Transcripciones
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <label htmlFor="consultation" className="block text-sm font-medium text-gray-700 mb-2">
          ID de Consulta
        </label>
        <div className="flex space-x-3">
          <input
            id="consultation"
            type="text"
            value={consultationId}
            onChange={(e) => setConsultationId(e.target.value)}
            placeholder="Ej: cons_43103"
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            style={{ backgroundColor: 'white', color: 'black' }}
            onKeyDown={(e) => e.key === 'Enter' && fetchFhir()}
          />
          <button
            onClick={fetchFhir}
            disabled={loading || !consultationId.trim()}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium disabled:opacity-50"
          >
            {loading ? 'Buscando...' : 'Buscar'}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 mb-6">
          {error}
        </div>
      )}

      {fhirData && (
        <div className="space-y-6">
          {totalEntities === 0 ? (
            <div className="bg-white rounded-xl shadow-sm p-8 text-center">
              <p className="text-gray-600">No se encontraron entidades FHIR en esta transcripción</p>
              <p className="text-gray-400 text-sm mt-2">
                La transcripción no contiene síntomas, medicamentos, signos vitales ni procedimientos reconocidos
              </p>
            </div>
          ) : (
            <>
              {entities?.conditions && entities.conditions.length > 0 && (
                <div className="bg-white rounded-xl shadow-sm overflow-hidden">
                  <div className="bg-red-50 px-6 py-4 border-b border-red-100">
                    <h2 className="text-lg font-semibold text-red-800">
                      Diagnósticos (Condition) - {entities.conditions.length}
                    </h2>
                  </div>
                  <div className="divide-y divide-gray-100">
                    {entities.conditions.map((c: FhirEntity, i: number) => (
                      <div key={i} className="px-6 py-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-medium text-gray-900">{c.display}</p>
                            <p className="text-sm text-gray-500">{c.text}</p>
                          </div>
                          <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">
                            SNOMED: {c.code}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {entities?.medications && entities.medications.length > 0 && (
                <div className="bg-white rounded-xl shadow-sm overflow-hidden">
                  <div className="bg-blue-50 px-6 py-4 border-b border-blue-100">
                    <h2 className="text-lg font-semibold text-blue-800">
                      Medicamentos (MedicationRequest) - {entities.medications.length}
                    </h2>
                  </div>
                  <div className="divide-y divide-gray-100">
                    {entities.medications.map((m: FhirEntity, i: number) => (
                      <div key={i} className="px-6 py-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-medium text-gray-900">{m.display}</p>
                            {m.dosage && (
                              <p className="text-sm text-gray-500">Dosis: {m.dosage}</p>
                            )}
                          </div>
                          <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">
                            RxNorm: {m.code}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {entities?.observations && entities.observations.length > 0 && (
                <div className="bg-white rounded-xl shadow-sm overflow-hidden">
                  <div className="bg-green-50 px-6 py-4 border-b border-green-100">
                    <h2 className="text-lg font-semibold text-green-800">
                      Signos Vitales (Observation) - {entities.observations.length}
                    </h2>
                  </div>
                  <div className="divide-y divide-gray-100">
                    {entities.observations.map((o: FhirEntity, i: number) => (
                      <div key={i} className="px-6 py-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-medium text-gray-900">{o.display}</p>
                            {o.value && (
                              <p className="text-sm text-gray-500">Valor: {o.value}</p>
                            )}
                          </div>
                          <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">
                            LOINC: {o.code}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {entities?.procedures && entities.procedures.length > 0 && (
                <div className="bg-white rounded-xl shadow-sm overflow-hidden">
                  <div className="bg-purple-50 px-6 py-4 border-b border-purple-100">
                    <h2 className="text-lg font-semibold text-purple-800">
                      Procedimientos (Procedure) - {entities.procedures.length}
                    </h2>
                  </div>
                  <div className="divide-y divide-gray-100">
                    {entities.procedures.map((p: FhirEntity, i: number) => (
                      <div key={i} className="px-6 py-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-medium text-gray-900">{p.display}</p>
                            <p className="text-sm text-gray-500">{p.text}</p>
                          </div>
                          <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">
                            SNOMED: {p.code}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
