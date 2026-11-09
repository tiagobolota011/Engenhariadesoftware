import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import App from './App'

function stubFetch(status: number, body: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(
      new Response(JSON.stringify(body), {
        status,
        headers: { 'Content-Type': 'application/json' },
      }),
    ),
  )
}

describe('App health status', () => {
  it('shows ok status', async () => {
    stubFetch(200, { status: 'ok', db: 'up' })
    render(<App />)
    expect(await screen.findByText('API: ok · DB: up')).toBeInTheDocument()
  })

  it('shows degraded on 503', async () => {
    stubFetch(503, { status: 'degraded', db: 'down' })
    render(<App />)
    expect(await screen.findByText('API: degraded · DB: down')).toBeInTheDocument()
  })

  it('shows unavailable when fetch rejects', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    render(<App />)
    expect(await screen.findByText('API indisponível')).toBeInTheDocument()
  })
})
