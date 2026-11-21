import { useEffect, useRef, useState } from 'react'

import { ChatInput } from '@/components/chat/ChatInput'
import { MessageBubble, TypingIndicator } from '@/components/chat/MessageBubble'
import type { Message } from '@/components/chat/types'
import { sendMessage } from '@/lib/chat'

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function handleSubmit(text: string) {
    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: 'user', content: text },
    ])
    setLoading(true)
    let reply: string
    try {
      reply = await sendMessage(text)
    } catch {
      reply = 'Something went wrong. Please try again.'
    }
    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: 'assistant', content: reply },
    ])
    setLoading(false)
  }

  if (messages.length === 0) {
    return (
      <main className="flex min-h-svh flex-col items-center justify-center gap-8 px-4">
        <h1 className="text-center text-3xl font-semibold tracking-tight">
          What can I help with?
        </h1>
        <div className="w-full max-w-3xl">
          <ChatInput onSubmit={handleSubmit} autoFocus />
        </div>
      </main>
    )
  }

  return (
    <main className="flex h-svh flex-col">
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-4 py-8">
          {messages.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}
          {loading && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>
      </div>
      <div className="mx-auto w-full max-w-3xl px-4 pt-2 pb-4">
        <ChatInput onSubmit={handleSubmit} disabled={loading} autoFocus />
      </div>
    </main>
  )
}

export default App
