'use client'

import Link from 'next/link'
import { useSession, signOut } from 'next-auth/react'

export function Header() {
  const { data: session, status } = useSession()

  return (
    <header className="bg-white shadow-sm border-b">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div className="flex items-center">
            <Link href="/" className="text-xl font-bold text-primary-600">
              Telemedicina
            </Link>
          </div>
          <div className="flex items-center space-x-4">
            {status === 'loading' ? (
              <span className="text-gray-500">Cargando...</span>
            ) : session ? (
              <>
                <Link href="/consultations" className="text-gray-600 hover:text-gray-900">
                  Consultas
                </Link>
                <Link href="/profiles" className="text-gray-600 hover:text-gray-900">
                  Perfiles
                </Link>
                <Link href="/dashboard" className="text-gray-600 hover:text-gray-900">
                  Dashboard
                </Link>
                <span className="text-sm text-gray-600">
                  {session.user?.email}
                </span>
                <button
                  onClick={() => signOut()}
                  className="text-gray-600 hover:text-gray-900"
                >
                  Cerrar sesión
                </button>
              </>
            ) : (
              <Link href="/auth/signin" className="btn-primary">
                Iniciar Sesión
              </Link>
            )}
          </div>
        </div>
      </nav>
    </header>
  )
}
