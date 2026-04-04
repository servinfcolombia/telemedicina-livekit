'use client'

import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

interface Transcription {
  consultation_id: string
  transcription: string | null
  language: string
  segments: any[]
  created_at: string | null
  created_by: string
  reviewed: boolean
  approved?: boolean
  reviewed_by?: string
  reviewed_at?: string
  corrections?: string
}

export default function TranscriptionsPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [transcriptions, setTranscriptions] = useState<Transcription[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [reviewingId, setReviewingId] = useState<string | null>(null)
  const [reviewApproved, setReviewApproved] = useState(true)
  const [reviewCorrections, setReviewCorrections] = useState('')

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin')
    }
  }, [status, router])

  useEffect(() => {
    if (session) {
      fetchTranscriptions()
    }
  }, [session])

  const fetchTranscriptions = async () => {
    try {
      const consultationsRes = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/consultations/`,
        {
          headers: {
            Authorization: `Bearer ${(session as any)?.accessToken}`,
          },
        }
      )

      if (!consultationsRes.ok) {
        console.error('Error fetching consultations')
        return
      }

      const consultations = await consultationsRes.json()
      const transcriptions: Transcription[] = []

      for (const consultation of consultations) {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/ia/transcriptions/${consultation.id}`,
          {
            headers: {
              Authorization: `Bearer ${(session as any)?.accessToken}`,
            },
          }
        )

        if (res.ok) {
          const data = await res.json()
          if (data.transcription) {
            transcriptions.push(data)
          }
        }
      }

      setTranscriptions(transcriptions)
    } catch (error) {
      console.error('Error fetching transcriptions:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleReview = async (consultationId: string) => {
    try {
      const formData = new FormData()
      formData.append('approved', String(reviewApproved))
      if (reviewCorrections) {
        formData.append('corrections', reviewCorrections)
      }

      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/ia/${consultationId}/review`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${(session as any)?.accessToken}`,
          },
          body: formData,
        }
      )

      if (res.ok) {
        setReviewingId(null)
        setReviewCorrections('')
        fetchTranscriptions()
      }
    } catch (error) {
      console.error('Error reviewing transcription:', error)
    }
  }

  const formatPreview = (text: string) => {
    if (!text || text.startsWith('Error en transcripción')) return text
    return text.length > 150 ? text.substring(0, 150) + '...' : text
  }

  const isError = (text: string) => text?.startsWith('Error en transcripción')

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
        <h1 className="text-3xl font-bold text-gray-900">Transcripciones</h1>
        <div className="flex space-x-3">
          <button
            onClick={() => router.push('/recordings')}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-medium"
          >
            Grabaciones
          </button>
          <button
            onClick={() => router.push('/consultations')}
            className="btn-primary"
          >
            Volver a Consultas
          </button>
        </div>
      </div>

      {transcriptions.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm p-8 text-center">
          <p className="text-gray-600">No hay transcripciones disponibles</p>
          <p className="text-gray-400 text-sm mt-2">
            Las transcripciones se generan automáticamente al finalizar una videoconsulta
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {transcriptions.map((t) => (
            <div key={t.consultation_id} className="bg-white rounded-xl shadow-sm overflow-hidden">
              <div
                className="p-4 cursor-pointer hover:bg-gray-50 flex items-center justify-between"
                onClick={() => setExpandedId(expandedId === t.consultation_id ? null : t.consultation_id)}
              >
                <div className="flex items-center space-x-4">
                  <span className="font-mono text-sm text-gray-600 bg-gray-100 px-2 py-1 rounded">
                    {t.consultation_id}
                  </span>
                  <div>
                    {isError(t.transcription || '') ? (
                      <span className="text-red-600 text-sm">Error en transcripción</span>
                    ) : (
                      <p className="text-gray-700 text-sm">{formatPreview(t.transcription || '')}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  {t.reviewed ? (
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      t.approved ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {t.approved ? 'Aprobada' : 'Rechazada'}
                    </span>
                  ) : (
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
                      Pendiente
                    </span>
                  )}
                  <svg
                    className={`w-5 h-5 text-gray-400 transition-transform ${expandedId === t.consultation_id ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>

              {expandedId === t.consultation_id && (
                <div className="border-t border-gray-200 p-4">
                  <div className="mb-4">
                    <div className="flex items-center space-x-4 text-sm text-gray-500 mb-2">
                      <span>Idioma: {t.language}</span>
                      {t.created_at && (
                        <span>Creada: {new Date(t.created_at).toLocaleString('es-ES')}</span>
                      )}
                    </div>

                    {isError(t.transcription || '') ? (
                      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
                        {t.transcription}
                      </div>
                    ) : (
                      <div className="bg-gray-50 rounded-lg p-4">
                        <p className="text-gray-800 whitespace-pre-wrap">{t.transcription}</p>
                      </div>
                    )}
                  </div>

                  {!t.reviewed && !isError(t.transcription || '') && (
                    <div className="border-t border-gray-200 pt-4">
                      {reviewingId === t.consultation_id ? (
                        <div className="space-y-3">
                          <div className="flex space-x-4">
                            <button
                              onClick={() => {
                                setReviewApproved(true)
                                handleReview(t.consultation_id)
                              }}
                              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
                            >
                              Aprobar
                            </button>
                            <button
                              onClick={() => setReviewApproved(false)}
                              className={`px-4 py-2 rounded-lg font-medium ${
                                !reviewApproved
                                  ? 'bg-red-600 text-white'
                                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                              }`}
                            >
                              Rechazar
                            </button>
                          </div>
                          {!reviewApproved && (
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                Correcciones (opcional)
                              </label>
                              <textarea
                                value={reviewCorrections}
                                onChange={(e) => setReviewCorrections(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                                rows={3}
                                placeholder="Ingresa las correcciones..."
                                style={{ backgroundColor: 'white', color: 'black' }}
                              />
                            </div>
                          )}
                          <div className="flex space-x-2">
                            {!reviewApproved && (
                              <button
                                onClick={() => handleReview(t.consultation_id)}
                                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium"
                              >
                                Enviar revisión
                              </button>
                            )}
                            <button
                              onClick={() => {
                                setReviewingId(null)
                                setReviewCorrections('')
                              }}
                              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 font-medium"
                            >
                              Cancelar
                            </button>
                          </div>
                        </div>
                      ) : (
                        <button
                          onClick={() => setReviewingId(t.consultation_id)}
                          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium"
                        >
                          Revisar transcripción
                        </button>
                      )}
                    </div>
                  )}

                  {t.reviewed && t.corrections && (
                    <div className="border-t border-gray-200 pt-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-1">Correcciones:</h4>
                      <p className="text-gray-600 text-sm whitespace-pre-wrap">{t.corrections}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
