export interface User {
  email: string
  name: string
  picture_url: string | null
  is_admin: boolean
}

// Returns the current user, or null when not logged in.
export async function fetchMe(): Promise<User | null> {
  const res = await fetch('/api/auth/me', { credentials: 'include' })
  if (res.status === 401) return null
  if (!res.ok) throw new Error(`Auth check failed (${res.status})`)
  return res.json()
}

// Login is an OAuth redirect flow, so navigate the whole page.
export function login() {
  window.location.href = '/api/auth/login'
}

export async function logout(): Promise<void> {
  const res = await fetch('/api/auth/logout', {
    method: 'POST',
    credentials: 'include',
  })
  if (!res.ok) throw new Error(`Logout failed (${res.status})`)
}
