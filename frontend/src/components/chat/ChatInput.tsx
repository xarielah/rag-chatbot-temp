import { useState, type KeyboardEvent } from 'react'
import { ArrowUp } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

type Props = {
  onSubmit: (text: string) => void
  disabled?: boolean
  autoFocus?: boolean
}

const MAX_LENGTH = 2000
const COUNTER_THRESHOLD = 1800

export function ChatInput({ onSubmit, disabled, autoFocus }: Props) {
  const [value, setValue] = useState('')
  const canSend = value.trim().length > 0 && !disabled

  function submit() {
    if (!canSend) return
    onSubmit(value.trim())
    setValue('')
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="relative flex items-end gap-2 rounded-3xl border bg-background p-2 pl-5 shadow-sm focus-within:ring-3 focus-within:ring-ring/30">
      {value.length >= COUNTER_THRESHOLD && (
        <span
          className={`absolute -top-6 right-4 text-xs ${
            value.length >= MAX_LENGTH ? 'text-destructive' : 'text-muted-foreground'
          }`}
        >
          {value.length}/{MAX_LENGTH}
        </span>
      )}
      <Textarea
        autoFocus={autoFocus}
        value={value}
        maxLength={MAX_LENGTH}
        onChange={(e) => setValue(e.target.value.slice(0, MAX_LENGTH))}
        onKeyDown={onKeyDown}
        placeholder="Ask anything"
        rows={1}
        className="max-h-48 min-h-9 py-1.5"
      />
      <Button
        type="button"
        size="icon"
        className="size-9 shrink-0 rounded-full"
        disabled={!canSend}
        onClick={submit}
        aria-label="Send message"
      >
        <ArrowUp />
      </Button>
    </div>
  )
}
