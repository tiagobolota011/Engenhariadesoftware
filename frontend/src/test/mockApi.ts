import { vi } from 'vitest'

type Reply = { status?: number; body?: unknown }
type Handler = (request: { url: URL; body: unknown }) => Reply

/** Substitui o fetch por respostas definidas por "MÉTODO /caminho". */
export function mockApi(routes: Record<string, Handler | Reply>) {
  const calls: { key: string; url: URL; body: unknown }[] = []
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), 'http://localhost')
    const method = (init?.method ?? 'GET').toUpperCase()
    const key = `${method} ${url.pathname}`
    const body = init?.body ? JSON.parse(String(init.body)) : undefined
    calls.push({ key, url, body })
    const route = routes[key]
    if (!route) return new Response(JSON.stringify({ detail: `no mock for ${key}` }), { status: 500 })
    const reply = typeof route === 'function' ? route({ url, body }) : route
    const status = reply.status ?? 200
    return new Response(status === 204 ? null : JSON.stringify(reply.body ?? {}), {
      status,
      headers: { 'Content-Type': 'application/json' },
    })
  })
  vi.stubGlobal('fetch', fetchMock)
  return { calls, count: (key: string) => calls.filter((c) => c.key === key).length }
}

export const mariana = {
  id: 1,
  username: 'mariana',
  name: 'Mariana Costa',
  role: 'customer',
  role_label: 'Customer',
  workspace: { id: 1, name: 'FeatureHub Demo' },
}

export const rui = { ...mariana, id: 3, username: 'rui', name: 'Rui Almeida', role: 'product_owner', role_label: 'Product Owner' }

export function requestItem(over: Record<string, unknown> = {}) {
  return {
    id: 42,
    key: 'REQ-042',
    title: 'Schedule an order in advance',
    category: { id: 4, name: 'Ordering' },
    tags: ['scheduling', 'mobile'],
    status: 'under_review',
    status_label: 'Under review',
    votes: 12,
    voted: false,
    my_role: null,
    author_name: 'Pedro Nunes',
    created_at: '2026-10-02T10:00:00+00:00',
    updated_at: '2026-10-09T10:00:00+00:00',
    ...over,
  }
}

export const page = (results: unknown[]) => ({ count: results.length, next: null, previous: null, results })
