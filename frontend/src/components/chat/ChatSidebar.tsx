import { PlusIcon, Trash2Icon } from 'lucide-react'

import { Button } from '@/components/ui/button'
import type { ChatSummary } from '@/lib/chats'
import { cn } from '@/lib/utils'

type Props = {
  chats: ChatSummary[]
  activeId: string | null
  open: boolean
  onClose: () => void
  onNewChat: () => void
  onSelect: (id: string) => void
  onDelete: (id: string) => void
}

export function ChatSidebar({
  chats,
  activeId,
  open,
  onClose,
  onNewChat,
  onSelect,
  onDelete,
}: Props) {
  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-20 bg-black/40 md:hidden"
          onClick={onClose}
          aria-hidden
        />
      )}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r bg-background transition-transform',
          open ? 'translate-x-0' : '-translate-x-full md:translate-x-0',
        )}
      >
        <div className="p-3 pt-4">
          <Button variant="outline" className="w-full justify-start" onClick={onNewChat}>
            <PlusIcon /> New chat
          </Button>
        </div>
        <nav className="flex-1 overflow-y-auto px-2 pb-4">
          {chats.length === 0 ? (
            <p className="px-2 py-3 text-sm text-muted-foreground">No previous chats</p>
          ) : (
            <ul className="flex flex-col gap-0.5">
              {chats.map((c) => (
                <li key={c.id} className="group relative">
                  <button
                    type="button"
                    onClick={() => onSelect(c.id)}
                    title={c.title ?? 'New chat'}
                    className={cn(
                      'w-full truncate rounded-md px-2 py-2 pr-8 text-left text-sm hover:bg-muted',
                      c.id === activeId && 'bg-muted font-medium',
                    )}
                  >
                    {c.title ?? 'New chat'}
                  </button>
                  <button
                    type="button"
                    aria-label="Delete chat"
                    onClick={() => onDelete(c.id)}
                    className="absolute top-1/2 right-1.5 -translate-y-1/2 rounded p-1 text-muted-foreground opacity-0 hover:text-foreground focus-visible:opacity-100 group-hover:opacity-100"
                  >
                    <Trash2Icon className="size-3.5" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </nav>
      </aside>
    </>
  )
}
