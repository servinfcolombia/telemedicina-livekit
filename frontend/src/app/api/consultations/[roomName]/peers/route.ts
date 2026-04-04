import { NextRequest, NextResponse } from 'next/server'

const roomPeers = new Map<string, { peerId: string; userName: string; roomName: string; joinedAt: number }>()

export async function GET(
  request: NextRequest,
  { params }: { params: { roomName: string } }
) {
  const roomName = params.roomName

  const now = Date.now()
  const activePeers = Array.from(roomPeers.entries())
    .filter(([_, peer]) => peer.roomName === roomName && (now - peer.joinedAt) < 30000)
    .map(([_, peer]) => peer.peerId)

  return NextResponse.json({ peers: activePeers })
}

export async function POST(
  request: NextRequest,
  { params }: { params: { roomName: string } }
) {
  const roomName = params.roomName
  const body = await request.json()
  const { peerId, userName } = body

  if (!peerId) {
    return NextResponse.json({ error: 'peerId required' }, { status: 400 })
  }

  roomPeers.set(peerId, {
    peerId,
    userName: userName || 'Unknown',
    roomName,
    joinedAt: Date.now(),
  })

  return NextResponse.json({ success: true })
}
