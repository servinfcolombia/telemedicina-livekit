import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Telemedicina - Plataforma de Consultas Virtuales',
  description: 'Plataforma de telemedicina para consultas médicas virtuales con videollamada en tiempo real',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es">
      <body className={inter.className}>
        <div className="min-h-screen bg-gray-50">
          <header className="bg-white shadow-sm border-b">
            <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16 items-center">
                <div className="flex items-center">
                  <a href="/" className="text-xl font-bold text-primary-600">
                    Telemedicina
                  </a>
                </div>
                <div className="flex items-center space-x-4">
                  <a href="/consultations" className="text-gray-600 hover:text-gray-900">
                    Consultas
                  </a>
                  <a href="/dashboard" className="text-gray-600 hover:text-gray-900">
                    Dashboard
                  </a>
                  <a href="/api/auth/signin" className="btn-primary">
                    Iniciar Sesión
                  </a>
                </div>
              </div>
            </nav>
          </header>
          <main>{children}</main>
        </div>
      </body>
    </html>
  )
}
