import { LogIn, LogOut } from 'lucide-react'

import { Button } from '@/components/ui/button'
import type { User } from '@/lib/auth'

interface UserMenuProps {
  user: User | null
  checking: boolean
  onLogin: () => void
  onLogout: () => void
}

export function UserMenu({ user, checking, onLogin, onLogout }: UserMenuProps) {
  if (checking) return null

  if (!user) {
    return (
      <Button variant="outline" size="sm" onClick={onLogin}>
        <LogIn /> Log in
      </Button>
    )
  }

  return (
    <div className="flex items-center gap-2">
      {user.picture_url ? (
        <img
          src={user.picture_url}
          alt=""
          referrerPolicy="no-referrer"
          className="size-7 rounded-full"
        />
      ) : (
        <div className="flex size-7 items-center justify-center rounded-full bg-muted text-xs font-medium">
          {user.name.charAt(0).toUpperCase()}
        </div>
      )}
      <Button variant="ghost" size="icon-sm" onClick={onLogout} title="Log out" aria-label="Log out">
        <LogOut />
      </Button>
    </div>
  )
}
