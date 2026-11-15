import { api } from './client'
import type { PriorityRow, Suggestion } from './types'

const query = (category: string) => (category ? `?category=${category}` : '')

export const listPriorities = (category = '') =>
  api<PriorityRow[]>(`/api/prioritization/${query(category)}`)

export const getSuggestion = (category = '') =>
  api<Suggestion>(`/api/prioritization/suggestion/${query(category)}`)

export const acceptSuggestion = (category = '') =>
  api<void>(`/api/prioritization/suggestion/accept/${query(category)}`, { method: 'POST' })

/** Coloca o pedido imediatamente antes de `before`; `null` = no fim da tabela. */
export const reorder = (request: number, before: number | null, reason: string) =>
  api<{ id: number; position: number }>('/api/prioritization/reorder/', {
    method: 'POST',
    body: { request, before, reason },
  })
