import { cn } from '@/lib/utils'
import type { Message } from './types'

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={cn(
          'whitespace-pre-wrap wrap-break-word text-[15px] leading-7',
          isUser
            ? 'max-w-[80%] rounded-3xl bg-muted px-5 py-2.5'
            : 'max-w-full',
        )}
      >
        {message.content}
      </div>
    </div>
  )
}

export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 py-3" aria-label="Assistant is typing">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="size-2 animate-pulse rounded-full bg-muted-foreground/60"
          style={{ animationDelay: `${i * 150}ms` }}
        />
      ))}
    </div>
  )
}
