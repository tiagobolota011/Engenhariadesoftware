import { api } from './client'
import type { User } from './types'

export const fetchMe = () => api<User>('/api/auth/me/')
export const login = (username: string, password: string) =>
  api<User>('/api/auth/login/', { method: 'POST', body: { username, password } })
export const logout = () => api<void>('/api/auth/logout/', { method: 'POST' })
