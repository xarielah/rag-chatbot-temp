import ReactMarkdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn } from '@/lib/utils'
import type { Message } from './types'

const markdownComponents: Components = {
  p: (props) => <p className="my-3 first:mt-0 last:mb-0" {...props} />,
  h1: (props) => <h1 className="mb-3 mt-5 text-2xl font-semibold first:mt-0" {...props} />,
  h2: (props) => <h2 className="mb-2 mt-5 text-xl font-semibold first:mt-0" {...props} />,
  h3: (props) => <h3 className="mb-2 mt-4 text-lg font-semibold first:mt-0" {...props} />,
  h4: (props) => <h4 className="mb-2 mt-4 font-semibold first:mt-0" {...props} />,
  ul: (props) => <ul className="my-3 list-disc space-y-1 pl-6" {...props} />,
  ol: (props) => <ol className="my-3 list-decimal space-y-1 pl-6" {...props} />,
  a: (props) => (
    <a
      className="text-primary underline underline-offset-2"
      target="_blank"
      rel="noopener noreferrer"
      {...props}
    />
  ),
  blockquote: (props) => (
    <blockquote className="my-3 border-l-4 border-border pl-4 text-muted-foreground" {...props} />
  ),
  hr: () => <hr className="my-4 border-border" />,
  pre: (props) => (
    <pre
      className="my-3 overflow-x-auto rounded-xl bg-muted p-4 font-mono text-sm leading-6 [&>code]:bg-transparent [&>code]:p-0"
      {...props}
    />
  ),
  code: (props) => (
    <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[0.9em]" {...props} />
  ),
  table: (props) => (
    <div className="my-3 overflow-x-auto">
      <table className="w-full border-collapse text-sm" {...props} />
    </div>
  ),
  th: (props) => (
    <th className="border border-border bg-muted px-3 py-1.5 text-left font-semibold" {...props} />
  ),
  td: (props) => <td className="border border-border px-3 py-1.5" {...props} />,
}

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={cn(
          'wrap-break-word text-[15px] leading-7',
          isUser
            ? 'max-w-[80%] whitespace-pre-wrap rounded-3xl bg-muted px-5 py-2.5'
            : 'max-w-full min-w-0',
        )}
      >
        {isUser ? (
          message.content
        ) : (
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
            {message.content}
          </ReactMarkdown>
        )}
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
