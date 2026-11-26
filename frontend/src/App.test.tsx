import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import App from './App'
import { mariana, mockApi, page, rui } from './test/mockApi'

const base = {
  'GET /api/requests/': { body: page([]) },
  'GET /api/categories/': { body: [] },
}

describe('App', () => {
  it('shows the login form when there is no session', async () => {
    mockApi({ 'GET /api/auth/me/': { status: 403, body: { detail: 'no' } } })
    render(<App />)
    expect(await screen.findByRole('button', { name: 'Sign in' })).toBeInTheDocument()
    expect(screen.queryByRole('navigation')).not.toBeInTheDocument()
  })

  it('signs in and shows the shell with name and role', async () => {
    const api = mockApi({
      ...base,
      'GET /api/auth/me/': { status: 403 },
      'GET /api/auth/csrf/': { body: { detail: 'ok' } },
      'POST /api/auth/login/': { body: mariana },
    })
    render(<App />)
    await userEvent.type(await screen.findByLabelText('Username'), 'mariana')
    await userEvent.type(screen.getByLabelText('Password'), 'featurehub')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(await screen.findByText('Mariana Costa')).toBeInTheDocument()
    expect(screen.getByText('Customer')).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'Feature Requests' })).toBeInTheDocument()
    expect(api.calls.find((c) => c.key === 'POST /api/auth/login/')?.body).toEqual({
      username: 'mariana',
      password: 'featurehub',
    })
  })

  it('shows the server message when the password is wrong', async () => {
    mockApi({
      'GET /api/auth/me/': { status: 403 },
      'GET /api/auth/csrf/': { body: {} },
      'POST /api/auth/login/': { status: 400, body: { detail: 'Invalid username or password.' } },
    })
    render(<App />)
    await userEvent.type(await screen.findByLabelText('Username'), 'mariana')
    await userEvent.type(screen.getByLabelText('Password'), 'x')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid username or password.')
  })

  it('hides team-only menu entries from customers', async () => {
    mockApi({ ...base, 'GET /api/auth/me/': { body: mariana } })
    render(<App />)
    const nav = await screen.findByRole('navigation')
    expect(nav).toHaveTextContent('My Requests')
    expect(nav).not.toHaveTextContent('Prioritization')
    expect(nav).not.toHaveTextContent('Backlog')
  })

  it('shows the unread notification count on the bell', async () => {
    mockApi({ ...base, 'GET /api/auth/me/': { body: rui }, 'GET /api/notifications/unread/': { body: { unread: 3 } } })
    render(<App />)
    expect(await screen.findByRole('link', { name: 'Notifications (3 unread)' })).toHaveTextContent('3')
  })

  it('shows the full menu to the product owner', async () => {
    mockApi({ ...base, 'GET /api/auth/me/': { body: rui } })
    render(<App />)
    const nav = await screen.findByRole('navigation')
    for (const label of ['Requests', 'My Requests', 'Prioritization', 'Backlog', 'User Stories', 'Traceability', 'Roadmap', 'Dashboard', 'Notifications']) {
      expect(nav).toHaveTextContent(label)
    }
  })
})
