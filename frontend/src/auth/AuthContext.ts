import { createContext, useContext } from 'react'
import type { User } from '../api/types'

export type Auth = {
  user: User | null
  signIn: (username: string, password: string) => Promise<void>
  signOut: () => Promise<void>
}

export const AuthContext = createContext<Auth | null>(null)

export function useAuth(): Auth {
  const auth = useContext(AuthContext)
  if (!auth) throw new Error('useAuth must be used inside an AuthContext provider')
  return auth
}

/** Utilizador com sessão iniciada (para páginas que só existem depois do login). */
export function useUser(): User {
  const { user } = useAuth()
  if (!user) throw new Error('This page needs a signed-in user')
  return user
}
