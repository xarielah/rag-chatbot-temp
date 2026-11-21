import { useState, type KeyboardEvent } from 'react'
import { ArrowUp } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

type Props = {
  onSubmit: (text: string) => void
  disabled?: boolean
  autoFocus?: boolean
}

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
    <div className="flex items-end gap-2 rounded-3xl border bg-background p-2 pl-5 shadow-sm focus-within:ring-3 focus-within:ring-ring/30">
      <Textarea
        autoFocus={autoFocus}
        value={value}
        onChange={(e) => setValue(e.target.value)}
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
