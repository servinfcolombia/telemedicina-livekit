'use client'

import { useState } from 'react'

interface ConsentProps {
  onConsent: (consent: boolean) => void
}

export function Consent({ onConsent }: ConsentProps) {
  const [agreed, setAgreed] = useState(false)
  const [showDetails, setShowDetails] = useState(false)

  const handleAccept = () => {
    if (agreed) {
      onConsent(true)
    }
  }

  return (
    <div className="card max-w-2xl mx-auto">
      <div className="text-center mb-6">
        <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-gray-900">
          Consentimiento Informado
        </h2>
        <p className="text-gray-500 mt-1">
          Por favor revise y acepte los términos antes de iniciar la consulta
        </p>
      </div>

      <div className={`bg-gray-50 rounded-lg p-4 mb-6 ${showDetails ? 'max-h-none' : 'max-h-48 overflow-hidden'}`}>
        <h3 className="font-medium text-gray-900 mb-2">Términos y Condiciones</h3>
        
        <div className="text-sm text-gray-600 space-y-4">
          <p>
            <strong>1. Consentimiento para Videoconsulta:</strong> Al aceptar, usted consiente 
            participar en una consulta médica virtual a través de videollamada.
          </p>
          
          <p>
            <strong>2. Grabación:</strong> Esta consulta puede ser grabada para fines de 
            documentación clínica y procesamiento de IA. La grabación se almacenará de 
            forma segura y cifrada.
          </p>
          
          <p>
            <strong>3. Privacidad:</strong> Sus datos médicos serán tratados conforme a la 
            normativa de protección de datos (HIPAA/LGPD). Sus informações personales serán 
            compartidas únicamente con el personal médico involucrado en su atención.
          </p>
          
          <p>
            <strong>4. Limitaciones:</strong> La videoconsulta no reemplaza completamente la 
            consulta presencial. En caso de emergencia, contacte servicios de emergencia 
            directamente.
          </p>
          
          <p>
            <strong>5. Transcripción:</strong> La consulta será transcrita automáticamente 
            mediante inteligencia artificial para generar notas clínicas. Un profesional 
            revisará la transcripción antes de integrarla a su historial.
          </p>
        </div>

        {showDetails && (
          <button
            onClick={() => setShowDetails(false)}
            className="text-primary-600 text-sm mt-2 hover:underline"
          >
            Ver menos
          </button>
        )}
        
        {!showDetails && (
          <button
            onClick={() => setShowDetails(true)}
            className="text-primary-600 text-sm mt-2 hover:underline"
          >
            Ver más detalles
          </button>
        )}
      </div>

      <div className="flex items-start space-x-3 mb-6">
        <input
          type="checkbox"
          id="consent"
          checked={agreed}
          onChange={(e) => setAgreed(e.target.checked)}
          className="mt-1 h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
        />
        <label htmlFor="consent" className="text-sm text-gray-700">
          He leído y acepto los términos y condiciones descritos anteriormente. 
          Consiento voluntariamente participar en esta videoconsulta y entiendo que 
          puede ser grabada y procesada con fines clínicos.
        </label>
      </div>

      <div className="flex justify-end space-x-3">
        <button
          onClick={() => onConsent(false)}
          className="btn-secondary"
        >
          Cancelar
        </button>
        <button
          onClick={handleAccept}
          disabled={!agreed}
          className={`btn-primary ${!agreed ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          Aceptar y Continuar
        </button>
      </div>
    </div>
  )
}
