import { api } from './client'
import type { Category, Comment, Page, PublicRoadmap, RequestDetail, RequestSummary } from './types'

export type ListFilters = {
  search?: string
  status?: string
  category?: string
  date?: string
  mine?: boolean
  page?: number
}

export function listRequests(filters: ListFilters = {}) {
  const params = new URLSearchParams()
  if (filters.search) params.set('search', filters.search)
  if (filters.status) params.set('status', filters.status)
  if (filters.category) params.set('category', filters.category)
  if (filters.date) params.set('date', filters.date)
  if (filters.mine) params.set('mine', '1')
  if (filters.page && filters.page > 1) params.set('page', String(filters.page))
  const query = params.toString()
  return api<Page<RequestSummary>>(`/api/requests/${query ? `?${query}` : ''}`)
}

export const listCategories = () => api<Category[]>('/api/categories/')

export const similarRequests = (title: string, tags: string[]) =>
  api<RequestSummary[]>(
    `/api/requests/similar/?${new URLSearchParams({ q: title, tags: tags.join(',') })}`,
  )

export type NewRequest = {
  title: string
  description: string
  category: number | null
  tags: string[]
  importance: string
}

export const createRequest = (body: NewRequest) =>
  api<RequestDetail>('/api/requests/', { method: 'POST', body })

export const getRequest = (id: number | string) => api<RequestDetail>(`/api/requests/${id}/`)

export const setVote = (id: number, voted: boolean) =>
  api<{ votes: number; voted: boolean }>(`/api/requests/${id}/vote/`, {
    method: voted ? 'POST' : 'DELETE',
  })

export const addComment = (id: number, body: string) =>
  api<Comment>(`/api/requests/${id}/comments/`, { method: 'POST', body: { body } })

export const markDecision = (id: number, commentId: number) =>
  api<Comment>(`/api/requests/${id}/comments/${commentId}/decision/`, { method: 'POST' })

export type AssessmentInput = {
  version: number
  impact: number | null
  effort: number | null
  status: string
}

export const saveAssessment = (id: number, body: AssessmentInput) =>
  api<RequestDetail>(`/api/requests/${id}/assessment/`, { method: 'PATCH', body })

export const publicRoadmap = () => api<PublicRoadmap>('/api/roadmap/public/')
