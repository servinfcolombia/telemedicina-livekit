'use client'

import { useState } from 'react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import { Consultation } from '@/types'

interface HistoryProps {
  consultations?: Consultation[]
  onSelect?: (consultation: Consultation) => void
}

export function History({ consultations = [], onSelect }: HistoryProps) {
  const [filter, setFilter] = useState<'all' | 'scheduled' | 'completed'>('all')

  const filteredConsultations = consultations.filter((c) => {
    if (filter === 'all') return true
    if (filter === 'scheduled') return c.status === 'scheduled'
    if (filter === 'completed') return c.status === 'finished'
    return true
  })

  const getStatusBadge = (status: Consultation['status']) => {
    const styles = {
      scheduled: 'bg-blue-100 text-blue-800',
      in_progress: 'bg-yellow-100 text-yellow-800',
      finished: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800',
    }

    const labels = {
      scheduled: 'Programada',
      in_progress: 'En Progreso',
      finished: 'Completada',
      cancelled: 'Cancelada',
    }

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status]}`}>
        {labels[status]}
      </span>
    )
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">
          Historial de Consultas
        </h2>
        
        <div className="flex space-x-2">
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1 rounded-full text-sm transition-colors ${
              filter === 'all'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Todas
          </button>
          <button
            onClick={() => setFilter('scheduled')}
            className={`px-3 py-1 rounded-full text-sm transition-colors ${
              filter === 'scheduled'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Programadas
          </button>
          <button
            onClick={() => setFilter('completed')}
            className={`px-3 py-1 rounded-full text-sm transition-colors ${
              filter === 'completed'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Completadas
          </button>
        </div>
      </div>

      {filteredConsultations.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-gray-400 mb-2">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <p className="text-gray-500">No hay consultas {filter !== 'all' ? 'con este filtro' : 'registradas'}</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredConsultations.map((consultation) => (
            <div
              key={consultation.id}
              onClick={() => onSelect?.(consultation)}
              className="border border-gray-200 rounded-lg p-4 hover:border-primary-300 transition-colors cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-gray-900">
                      Consulta #{consultation.id}
                    </span>
                    {getStatusBadge(consultation.status)}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    {format(new Date(consultation.scheduledAt), "EEEE d 'de' MMMM 'de' yyyy", { locale: es })}
                    {' • '}
                    {consultation.durationMinutes} minutos
                  </p>
                </div>
                
                {consultation.status === 'scheduled' && (
                  <button className="btn-primary text-sm py-2">
                    Unirse
                  </button>
                )}
              </div>

              {consultation.notes && (
                <p className="mt-2 text-sm text-gray-600 line-clamp-2">
                  {consultation.notes}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
