// Goes through the /api/* proxy (Vercel rewrite / nginx), so the backend route is /api/chat.
export async function sendMessage(text: string): Promise<string> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: text }),
  })
  if (!res.ok) {
    throw new Error(`Chat request failed (${res.status})`)
  }
  const data = await res.json()
  return data.response ?? data.answer ?? ''
}
