import { NextResponse } from 'next/server'

export async function GET() {
  try {
    const response = await fetch('http://localhost:8000/api/livekit/ice-servers')
    if (!response.ok) {
      throw new Error('Failed to get ICE servers from backend')
    }
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching ICE servers:', error)
    return NextResponse.json(
      { iceServers: [] },
      { status: 500 }
    )
  }
}
