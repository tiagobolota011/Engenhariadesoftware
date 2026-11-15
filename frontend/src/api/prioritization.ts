import { api } from './client'
import type { PriorityRow, Suggestion } from './types'

const query = (category: string) => (category ? `?category=${category}` : '')

export const listPriorities = (category = '') =>
  api<PriorityRow[]>(`/api/prioritization/${query(category)}`)

export const getSuggestion = (category = '') =>
  api<Suggestion>(`/api/prioritization/suggestion/${query(category)}`)

export const acceptSuggestion = (category = '') =>
  api<void>(`/api/prioritization/suggestion/accept/${query(category)}`, { method: 'POST' })

export const reorder = (request: number, position: number, reason: string) =>
  api<{ id: number; position: number }>('/api/prioritization/reorder/', {
    method: 'POST',
    body: { request, position, reason },
  })
