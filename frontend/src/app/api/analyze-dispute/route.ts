import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  const body = await request.json()

  const response = await fetch('http://localhost:8000/api/analyze-dispute', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })

  const data = await response.json()
  return NextResponse.json(data)
}

