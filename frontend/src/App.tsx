import { useEffect, useRef, useState } from 'react'

import { ChatInput } from '@/components/chat/ChatInput'
import { MessageBubble, TypingIndicator } from '@/components/chat/MessageBubble'
import type { Message } from '@/components/chat/types'
import { UserMenu } from '@/components/auth/UserMenu'
import { fetchMe, login, logout, type User } from '@/lib/auth'
import { MenuIcon } from 'lucide-react'

import { ChatSidebar } from '@/components/chat/ChatSidebar'
import { Button } from '@/components/ui/button'
import { ChatError, fetchChatMessages, sendMessage } from '@/lib/chat'
import { deleteChat, listChats, type ChatSummary } from '@/lib/chats'

const CHAT_PATH = /^\/chat\/([^/]+)\/?$/

function chatIdFromPath(): string | null {
  const m = CHAT_PATH.exec(window.location.pathname)
  return m ? decodeURIComponent(m[1]) : null
}

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [chatId, setChatId] = useState<string | null>(chatIdFromPath)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [chats, setChats] = useState<ChatSummary[]>([])
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [user, setUser] = useState<User | null>(null)
  const [checking, setChecking] = useState(true)
  const bottomRef = useRef<HTMLDivElement>(null)
  // Chat id created locally in this session: its messages are already in state, no reload needed.
  const skipLoadRef = useRef<string | null>(null)

  // Back/forward between chat URLs.
  useEffect(() => {
    function onPopState() {
      const id = chatIdFromPath()
      if (id === null) setMessages([])
      setChatId(id)
    }
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  // Load stored messages when a chat id is present (deep link, reload, back/forward).
  useEffect(() => {
    if (!user || !chatId) return
    if (skipLoadRef.current === chatId) {
      // Created locally: messages are already in state. Reload normally next time.
      skipLoadRef.current = null
      return
    }
    let cancelled = false
    setHistoryLoading(true)
    fetchChatMessages(chatId)
      .then((stored) => {
        if (cancelled) return
        setMessages(
          stored.map((m) => ({
            id: String(m.id),
            role: m.role,
            content: m.content,
          })),
        )
      })
      .catch((err) => {
        if (cancelled) return
        setMessages([])
        setChatId(null)
        window.history.replaceState(null, '', '/')
        if (!(err instanceof ChatError && err.kind === 'gone')) {
          setMessages([
            {
              id: crypto.randomUUID(),
              role: 'assistant',
              content: 'Could not load this chat. Please try again.',
            },
          ])
        }
      })
      .finally(() => {
        if (!cancelled) setHistoryLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [user, chatId])

  useEffect(() => {
    fetchMe()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setChecking(false))
  }, [])

  function refreshChats() {
    listChats()
      .then(setChats)
      .catch(() => {})
  }

  useEffect(() => {
    if (user) refreshChats()
  }, [user])

  async function handleLogout() {
    try {
      await logout()
    } finally {
      setUser(null)
      setChats([])
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
      if (res.chatId !== chatId) {
        skipLoadRef.current = res.chatId
        setChatId(res.chatId)
        window.history.pushState(null, '', `/chat/${encodeURIComponent(res.chatId)}`)
      }
      reply = res.reply
    } catch (err) {
      if (err instanceof ChatError && err.kind === 'budget') {
        // Next message starts a fresh chat.
        setChatId(null)
        window.history.replaceState(null, '', '/')
        reply =
          'This chat reached its token limit. Your next message will start a new chat.'
      } else if (err instanceof ChatError && err.kind === 'gone') {
        setChatId(null)
        window.history.replaceState(null, '', '/')
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
    refreshChats()
  }

  function startNewChat() {
    setSidebarOpen(false)
    if (chatId === null && messages.length === 0) return
    setMessages([])
    setChatId(null)
    window.history.pushState(null, '', '/')
  }

  function openChat(id: string) {
    setSidebarOpen(false)
    if (id === chatId) return
    setMessages([])
    setChatId(id)
    window.history.pushState(null, '', `/chat/${encodeURIComponent(id)}`)
  }

  async function handleDeleteChat(id: string) {
    if (!window.confirm('Delete this chat?')) return
    try {
      await deleteChat(id)
    } catch {
      return
    }
    setChats((prev) => prev.filter((c) => c.id !== id))
    if (id === chatId) startNewChat()
  }

  const header = (
    <header
      className={`fixed inset-x-0 top-0 z-10 flex h-14 items-center justify-between bg-transparent px-4 backdrop-blur-md ${user ? 'md:left-64' : ''}`}
    >
      {user ? (
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          aria-label="Open chat list"
          onClick={() => setSidebarOpen(true)}
        >
          <MenuIcon />
        </Button>
      ) : (
        <span />
      )}
      <UserMenu
        user={user}
        checking={checking}
        onLogin={login}
        onLogout={handleLogout}
      />
    </header>
  )

  const firstName = user?.name.trim().split(/\s+/)[0]

  const sidebar = user && (
    <ChatSidebar
      chats={chats}
      activeId={chatId}
      open={sidebarOpen}
      onClose={() => setSidebarOpen(false)}
      onNewChat={startNewChat}
      onSelect={openChat}
      onDelete={handleDeleteChat}
    />
  )
  const shift = user ? 'md:pl-64' : ''

  if (messages.length === 0 && !chatId) {
    return (
      <>
        {sidebar}
        <main
          className={`relative flex min-h-svh flex-col items-center justify-center gap-8 px-4 ${shift}`}
        >
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
      </>
    )
  }

  return (
    <>
    {sidebar}
    <main className={`relative flex h-svh flex-col ${shift}`}>
      {header}
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-4 pt-20 pb-8">
          {messages.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}
          {(loading || historyLoading) && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>
      </div>
      <div className="mx-auto w-full max-w-3xl px-4 pt-2 pb-4">
        <ChatInput onSubmit={handleSubmit} disabled={loading} autoFocus />
      </div>
    </main>
    </>
  )
}

export default App
