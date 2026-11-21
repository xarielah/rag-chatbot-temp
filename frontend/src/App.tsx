import { useEffect, useRef, useState } from 'react'

import { ChatInput } from '@/components/chat/ChatInput'
import { MessageBubble, TypingIndicator } from '@/components/chat/MessageBubble'
import type { Message } from '@/components/chat/types'
import { UserMenu } from '@/components/auth/UserMenu'
import { fetchMe, login, logout, type User } from '@/lib/auth'
import { ChatError, sendMessage } from '@/lib/chat'

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [chatId, setChatId] = useState<string | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [checking, setChecking] = useState(true)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchMe()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setChecking(false))
  }, [])

  async function handleLogout() {
    try {
      await logout()
    } finally {
      setUser(null)
    }
  }

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
      const res = await sendMessage(text, chatId)
      setChatId(res.chatId)
      reply = res.reply
    } catch (err) {
      if (err instanceof ChatError && err.kind === 'budget') {
        // Next message starts a fresh chat.
        setChatId(null)
        reply =
          'This chat reached its token limit. Your next message will start a new chat.'
      } else if (err instanceof ChatError && err.kind === 'gone') {
        setChatId(null)
        reply =
          'This chat has expired. Your next message will start a new chat.'
      } else {
        reply = 'Something went wrong. Please try again.'
      }
    }
    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: 'assistant', content: reply },
    ])
    setLoading(false)
  }

  const header = (
    <header className="fixed inset-x-0 top-0 z-10 flex h-14 items-center justify-end bg-transparent px-4 backdrop-blur-md">
      <UserMenu
        user={user}
        checking={checking}
        onLogin={login}
        onLogout={handleLogout}
      />
    </header>
  )

  const firstName = user?.name.trim().split(/\s+/)[0]

  if (messages.length === 0) {
    return (
      <main className="relative flex min-h-svh flex-col items-center justify-center gap-8 px-4">
        {header}

        <h1 className="text-center text-3xl font-semibold tracking-tight">
          {firstName && <div>Hi {firstName},</div>}
          What can I help you with?
        </h1>
        <div className="w-full max-w-3xl">
          <ChatInput
            onSubmit={handleSubmit}
            disabled={checking || !user}
            autoFocus
          />
          {!checking && !user && (
            <p className="mt-3 text-center text-sm text-muted-foreground">
              <button
                type="button"
                onClick={login}
                className="font-medium text-foreground underline underline-offset-4"
              >
                Log in
              </button>{' '}
              to start chatting.
            </p>
          )}
        </div>
      </main>
    )
  }

  return (
    <main className="relative flex h-svh flex-col">
      {header}
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-4 pt-20 pb-8">
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
