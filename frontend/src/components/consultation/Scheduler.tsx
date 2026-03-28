'use client'

import { useState } from 'react'
import { format, addDays } from 'date-fns'
import { es } from 'date-fns/locale'

interface SchedulerProps {
  onSchedule?: (date: Date, duration: number) => void
}

export function Scheduler({ onSchedule }: SchedulerProps) {
  const [selectedDate, setSelectedDate] = useState<Date>(addDays(new Date(), 1))
  const [selectedTime, setSelectedTime] = useState<string>('09:00')
  const [duration, setDuration] = useState<number>(30)
  const [notes, setNotes] = useState<string>('')

  const timeSlots = [
    '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
    '12:00', '12:30', '14:00', '14:30', '15:00', '15:30',
    '16:00', '16:30', '17:00', '17:30'
  ]

  const dates = Array.from({ length: 7 }, (_, i) => addDays(new Date(), i + 1))

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const [hours, minutes] = selectedTime.split(':').map(Number)
    const scheduledDate = new Date(selectedDate)
    scheduledDate.setHours(hours, minutes, 0, 0)
    
    onSchedule?.(scheduledDate, duration)
  }

  return (
    <div className="card">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">
        Programar Nueva Consulta
      </h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Seleccionar Fecha
          </label>
          <div className="grid grid-cols-7 gap-2">
            {dates.map((date) => (
              <button
                key={date.toISOString()}
                type="button"
                onClick={() => setSelectedDate(date)}
                className={`p-3 rounded-lg text-center transition-colors ${
                  selectedDate.toDateString() === date.toDateString()
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                }`}
              >
                <div className="text-xs">{format(date, 'EEE', { locale: es })}</div>
                <div className="text-lg font-semibold">{format(date, 'd')}</div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Seleccionar Hora
          </label>
          <div className="grid grid-cols-4 gap-2">
            {timeSlots.map((time) => (
              <button
                key={time}
                type="button"
                onClick={() => setSelectedTime(time)}
                className={`px-4 py-2 rounded-lg text-sm transition-colors ${
                  selectedTime === time
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                }`}
              >
                {time}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Duración de la Consulta
          </label>
          <select
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
            className="input-field"
          >
            <option value={15}>15 minutos</option>
            <option value={30}>30 minutos</option>
            <option value={45}>45 minutos</option>
            <option value={60}>60 minutos</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Notas (opcional)
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Describe el motivo de la consulta..."
            rows={3}
            className="input-field"
          />
        </div>

        <div className="flex justify-end space-x-3">
          <button type="button" className="btn-secondary">
            Cancelar
          </button>
          <button type="submit" className="btn-primary">
            Programar Consulta
          </button>
        </div>
      </form>
    </div>
  )
}
