'use client'

import { useState, useEffect } from 'react'
import { Transcription, FHIRBundle } from '@/types'

interface ReviewItem {
  id: string
  consultationId: string
  transcription: string
  fhirBundle?: FHIRBundle
  confidence: number
  reviewed: boolean
  approved: boolean
  reviewedBy?: string
  reviewedAt?: string
  createdAt: string
}

export function ReviewDashboard() {
  const [items, setItems] = useState<ReviewItem[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedItem, setSelectedItem] = useState<ReviewItem | null>(null)
  const [filter, setFilter] = useState<'pending' | 'reviewed'>('pending')

  useEffect(() => {
    loadItems()
  }, [filter])

  const loadItems = async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/ia/pending-review?filter=${filter}`)
      const data = await response.json()
      setItems(data)
    } catch (error) {
      console.error('Error loading items:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleReview = async (item: ReviewItem, approved: boolean, corrections?: string) => {
    try {
      await fetch(`/api/ia/${item.id}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved, corrections }),
      })
      loadItems()
      setSelectedItem(null)
    } catch (error) {
      console.error('Error reviewing item:', error)
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600 bg-green-100'
    if (confidence >= 0.7) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Dashboard de Revisión de IA
        </h1>
        
        <div className="flex space-x-2">
          <button
            onClick={() => setFilter('pending')}
            className={`px-4 py-2 rounded-lg ${
              filter === 'pending'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Pendientes
          </button>
          <button
            onClick={() => setFilter('reviewed')}
            className={`px-4 py-2 rounded-lg ${
              filter === 'reviewed'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Revisados
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-2">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-gray-500 text-lg">
            {filter === 'pending' ? 'No hay transcripciones pendientes de revisión' : 'No hay transcripciones revisadas'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-4">
            {items.map((item) => (
              <div
                key={item.id}
                onClick={() => setSelectedItem(item)}
                className={`card cursor-pointer transition-all ${
                  selectedItem?.id === item.id
                    ? 'ring-2 ring-primary-500'
                    : 'hover:shadow-md'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-900">
                    Consulta #{item.consultationId}
                  </span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(item.confidence)}`}>
                    {(item.confidence * 100).toFixed(0)}% confianza
                  </span>
                </div>
                
                <p className="text-sm text-gray-500 line-clamp-2 mb-2">
                  {item.transcription}
                </p>
                
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>{new Date(item.createdAt).toLocaleDateString()}</span>
                  {item.reviewed && (
                    <span className={item.approved ? 'text-green-600' : 'text-red-600'}>
                      {item.approved ? 'Aprobado' : 'Rechazado'}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {selectedItem && (
            <div className="card sticky top-4">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Revisar Transcripción
              </h2>
              
              <div className="mb-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Transcripción</h3>
                <div className="bg-gray-50 rounded-lg p-4 max-h-48 overflow-y-auto">
                  <p className="text-sm text-gray-700">{selectedItem.transcription}</p>
                </div>
              </div>

              {selectedItem.fhirBundle && (
                <div className="mb-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">
                    Entidades FHIR Extraídas
                  </h3>
                  <div className="bg-gray-50 rounded-lg p-4 max-h-48 overflow-y-auto">
                    {selectedItem.fhirBundle.entry?.map((entry, index) => {
                      const resource = entry.resource as { resourceType?: string; code?: { coding?: Array<{ display?: string; code?: string }> } };
                      return (
                        <div key={index} className="mb-2 pb-2 border-b border-gray-200 last:border-0">
                          <span className="font-medium text-gray-900">{resource.resourceType}</span>
                          {resource.code?.coding?.[0] && (
                            <p className="text-sm text-gray-600">
                              {resource.code.coding[0].display} ({resource.code.coding[0].code})
                            </p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {!selectedItem.reviewed && (
                <div className="flex space-x-3">
                  <button
                    onClick={() => handleReview(selectedItem, false)}
                    className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                  >
                    Rechazar
                  </button>
                  <button
                    onClick={() => handleReview(selectedItem, true)}
                    className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    Aprobar
                  </button>
                </div>
              )}
              
              {selectedItem.reviewed && (
                <div className="text-center py-4">
                  <span className={`font-medium ${selectedItem.approved ? 'text-green-600' : 'text-red-600'}`}>
                    {selectedItem.approved ? 'Transcripción aprobada' : 'Transcripción rechazada'}
                  </span>
                  <p className="text-sm text-gray-500 mt-1">
                    Revisado por {selectedItem.reviewedBy} el {new Date(selectedItem.reviewedAt!).toLocaleString()}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
