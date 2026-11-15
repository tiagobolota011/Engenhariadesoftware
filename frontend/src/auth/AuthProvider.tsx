import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { fetchMe, login, logout } from '../api/auth'
import { SESSION_LOST } from '../api/client'
import type { User } from '../api/types'
import { AuthContext } from './AuthContext'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [checking, setChecking] = useState(true)

  const refresh = useCallback(
    () =>
      fetchMe()
        .then(setUser)
        .catch(() => setUser(null)),
    [],
  )

  useEffect(() => {
    refresh().finally(() => setChecking(false))
    // Um 403 numa chamada pode ser sessão expirada: confirma-se com /auth/me/.
    const onLost = () => void refresh()
    window.addEventListener(SESSION_LOST, onLost)
    return () => window.removeEventListener(SESSION_LOST, onLost)
  }, [refresh])

  const auth = useMemo(
    () => ({
      user,
      signIn: async (username: string, password: string) => setUser(await login(username, password)),
      signOut: async () => {
        await logout().catch(() => undefined)
        setUser(null)
      },
    }),
    [user],
  )

  if (checking) return <p className="loading">Loading…</p>
  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>
}
