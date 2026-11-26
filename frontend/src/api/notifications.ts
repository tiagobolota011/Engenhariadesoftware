import { api } from './client'
import type { AppNotification, Member, NotificationList } from './types'

/** Evento para o contador do topo voltar a ler o número de não lidas. */
export const NOTIFICATIONS_CHANGED = 'featurehub:notifications-changed'
export const notificationsChanged = () => window.dispatchEvent(new Event(NOTIFICATIONS_CHANGED))

export const listNotifications = (unreadOnly = false) =>
  api<NotificationList>(`/api/notifications/${unreadOnly ? '?unread=1' : ''}`)

export const unreadCount = () => api<{ unread: number }>('/api/notifications/unread/')

export const markRead = (id: number) =>
  api<AppNotification>(`/api/notifications/${id}/read/`, { method: 'POST' })

export const markAllRead = () => api<{ unread: number }>('/api/notifications/read-all/', { method: 'POST' })

export const listMembers = () => api<Member[]>('/api/members/')
