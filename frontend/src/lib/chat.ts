// Goes through the /api/* proxy (Vercel rewrite / nginx), so the backend route is /api/chat.
export type ChatReply = {
  reply: string
  chatId: string
  tokensUsed: number
  tokenBudget: number
}

export class ChatError extends Error {
  // 'budget' = chat hit its token cap, 'gone' = chat expired / not found, 'other' = anything else
  kind: 'budget' | 'gone' | 'other'
  constructor(kind: 'budget' | 'gone' | 'other', message: string) {
    super(message)
    this.kind = kind
  }
}

export type StoredMessage = {
  id: number
  role: 'user' | 'assistant'
  content: string
}

export async function fetchChatMessages(chatId: string): Promise<StoredMessage[]> {
  const res = await fetch(`/api/chats/${encodeURIComponent(chatId)}/messages`)
  if (res.status === 404 || res.status === 422) {
    throw new ChatError('gone', 'Chat not found')
  }
  if (!res.ok) {
    throw new ChatError('other', `Loading chat failed (${res.status})`)
  }
  return res.json()
}

export async function sendMessage(
  text: string,
  chatId: string | null,
): Promise<ChatReply> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: text, chat_id: chatId }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    if (res.status === 429 && body?.detail?.code === 'chat_token_budget_exceeded') {
      throw new ChatError('budget', body.detail.message)
    }
    if (res.status === 404) {
      throw new ChatError('gone', 'Chat not found')
    }
    throw new ChatError('other', `Chat request failed (${res.status})`)
  }
  const data = await res.json()
  return {
    reply: data.response ?? data.answer ?? '',
    chatId: data.chat_id,
    tokensUsed: data.tokens_used,
    tokenBudget: data.token_budget,
  }
}
