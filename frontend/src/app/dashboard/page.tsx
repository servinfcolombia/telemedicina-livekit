'use client'

import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

interface DashboardStats {
  totalConsultations: number
  pendingConsultations: number
  completedConsultations: number
}

export default function DashboardPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [stats, setStats] = useState<DashboardStats>({
    totalConsultations: 0,
    pendingConsultations: 0,
    completedConsultations: 0,
  })

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin')
    }
  }, [status, router])

  useEffect(() => {
    if (session) {
      fetchDashboardData()
    }
  }, [session])

  const fetchDashboardData = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/consultations/`, {
        headers: {
          Authorization: `Bearer ${(session as any)?.accessToken}`,
        },
      })
      if (res.ok) {
        const data = await res.json()
        setStats({
          totalConsultations: data.length,
          pendingConsultations: data.filter((c: any) => c.status === 'scheduled').length,
          completedConsultations: data.filter((c: any) => c.status === 'finished').length,
        })
      }
    } catch (error) {
      console.error('Error fetching dashboard:', error)
    }
  }

  if (status === 'loading') {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-xl shadow-sm p-6">
          <p className="text-sm text-gray-600 mb-1">Total Consultas</p>
          <p className="text-3xl font-bold text-gray-900">{stats.totalConsultations}</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-6">
          <p className="text-sm text-gray-600 mb-1">Pendientes</p>
          <p className="text-3xl font-bold text-blue-600">{stats.pendingConsultations}</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-6">
          <p className="text-sm text-gray-600 mb-1">Completadas</p>
          <p className="text-3xl font-bold text-green-600">{stats.completedConsultations}</p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Bienvenido</h2>
        <p className="text-gray-600">
          {session?.user?.email}
        </p>
        <p className="text-gray-500 mt-2">
          Rol: {(session?.user as any)?.role || 'Paciente'}
        </p>
      </div>
    </div>
  )
}
