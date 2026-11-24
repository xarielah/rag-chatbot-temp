export type ChatSummary = {
  id: string
  title: string | null
  lastMessageAt: string
}

export async function listChats(): Promise<ChatSummary[]> {
  const res = await fetch('/api/chats')
  if (!res.ok) throw new Error(`Listing chats failed (${res.status})`)
  const data = await res.json()
  return data.map((c: { id: string; title: string | null; last_message_at: string }) => ({
    id: c.id,
    title: c.title,
    lastMessageAt: c.last_message_at,
  }))
}

export async function deleteChat(chatId: string): Promise<void> {
  const res = await fetch(`/api/chats/${encodeURIComponent(chatId)}`, {
    method: 'DELETE',
  })
  if (!res.ok && res.status !== 404) {
    throw new Error(`Deleting chat failed (${res.status})`)
  }
}
