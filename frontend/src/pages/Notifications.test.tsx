import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { AuthContext } from '../auth/AuthContext'
import type { User } from '../api/types'
import { mariana, mockApi, rui } from '../test/mockApi'
import Notifications from './Notifications'
import RequestDetail from './RequestDetail'

function notification(over: Record<string, unknown> = {}) {
  return {
    id: 7,
    kind: 'mention',
    kind_label: 'Mention',
    message: 'Mariana Costa mentioned you on REQ-042 Schedule an order in advance',
    actor_name: 'Mariana Costa',
    request_id: 42,
    read: false,
    created_at: '2026-11-26T10:00:00+00:00',
    ...over,
  }
}

function renderAt(path: string, user: unknown = rui) {
  return render(
    <AuthContext.Provider value={{ user: user as User, signIn: async () => {}, signOut: async () => {} }}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/notifications" element={<Notifications />} />
          <Route path="/requests/:id" element={<p>Request page</p>} />
          <Route path="/detail/:id" element={<RequestDetail />} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

describe('Notifications', () => {
  it('lists notifications with unread ones marked as new', async () => {
    mockApi({
      'GET /api/notifications/': {
        body: {
          unread: 1,
          results: [
            notification(),
            notification({ id: 6, kind: 'status', kind_label: 'Status change', message: 'REQ-040 Pay later is now Approved', read: true }),
          ],
        },
      },
    })
    renderAt('/notifications')
    const items = await screen.findAllByRole('listitem')
    expect(items).toHaveLength(2)
    expect(items[0]).toHaveTextContent('Mariana Costa mentioned you on REQ-042')
    expect(within(items[0]).getByText('New · Mention')).toBeInTheDocument()
    expect(within(items[1]).getByText('Status change')).toBeInTheDocument()
    expect(screen.getByText('1 unread notification')).toBeInTheDocument()
  })

  it('marks a notification as read and opens its request', async () => {
    const api = mockApi({
      'GET /api/notifications/': { body: { unread: 1, results: [notification()] } },
      'GET /api/notifications/unread/': { body: { unread: 0 } },
      'GET /api/auth/csrf/': { body: {} },
      'POST /api/notifications/7/read/': { body: notification({ read: true }) },
    })
    renderAt('/notifications')
    await userEvent.click(await screen.findByRole('button', { name: /mentioned you on REQ-042/ }))
    expect(await screen.findByText(/Request page/)).toBeInTheDocument()
    expect(api.count('POST /api/notifications/7/read/')).toBe(1)
  })

  it('marks all as read and filters unread only', async () => {
    let unread = 1
    const api = mockApi({
      'GET /api/notifications/': ({ url }) => ({
        body: {
          unread,
          results: url.searchParams.get('unread') === '1' && unread === 0 ? [] : [notification({ read: unread === 0 })],
        },
      }),
      'GET /api/auth/csrf/': { body: {} },
      'POST /api/notifications/read-all/': () => {
        unread = 0
        return { body: { unread: 0 } }
      },
    })
    renderAt('/notifications')
    await userEvent.click(await screen.findByRole('button', { name: 'Mark all as read' }))
    expect(await screen.findByText('0 unread notifications')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Mark all as read' })).toBeDisabled()
    await userEvent.click(screen.getByLabelText('Unread only'))
    expect(await screen.findByText('You are all caught up.')).toBeInTheDocument()
    expect(api.calls.at(-1)!.url.searchParams.get('unread')).toBe('1')
  })

  it('shows an empty state and a load error', async () => {
    mockApi({ 'GET /api/notifications/': { body: { unread: 0, results: [] } } })
    const { unmount } = renderAt('/notifications')
    expect(await screen.findByText(/No notifications yet/)).toBeInTheDocument()
    unmount()
    mockApi({ 'GET /api/notifications/': { status: 500, body: {} } })
    renderAt('/notifications')
    expect(await screen.findByRole('alert')).toHaveTextContent('could not be loaded')
  })
})

describe('Mentions in the request discussion', () => {
  const detail = {
    id: 42,
    key: 'REQ-042',
    title: 'Schedule an order in advance',
    category: { id: 4, name: 'Ordering' },
    tags: [],
    status: 'under_review',
    status_label: 'Under review',
    votes: 0,
    voted: false,
    my_role: 'created',
    author_name: 'Mariana Costa',
    created_at: '2026-10-02T10:00:00+00:00',
    updated_at: '2026-10-09T10:00:00+00:00',
    description: 'Choose a delivery date.',
    importance: '',
    version: 1,
    comments: [
      { id: 1, author_name: 'Mariana Costa', author_role: 'Customer', body: 'Can @rui decide? Mail me@x.pt', is_decision: false, created_at: '2026-10-09T09:00:00+00:00' },
    ],
    versions: [],
    assessment: null,
    can_assess: false,
    next_statuses: [],
  }
  const members = [
    { username: 'mariana', name: 'Mariana Costa', role_label: 'Customer' },
    { username: 'rui', name: 'Rui Almeida', role_label: 'Product Owner' },
  ]

  it('highlights mentions and inserts a teammate into the comment', async () => {
    const api = mockApi({
      'GET /api/requests/42/': { body: detail },
      'GET /api/members/': { body: members },
      'GET /api/auth/csrf/': { body: {} },
      'POST /api/requests/42/comments/': ({ body }) => ({
        status: 201,
        body: { id: 2, author_name: 'Mariana Costa', author_role: 'Customer', body: (body as { body: string }).body, is_decision: false, created_at: '2026-10-10T09:00:00+00:00' },
      }),
    })
    renderAt('/detail/42', mariana)
    const mention = await screen.findByText('@rui', { selector: '.mention' })
    expect(mention.closest('p')).toHaveTextContent('Can @rui decide? Mail me@x.pt')
    // A própria pessoa não aparece na sugestão.
    expect(screen.queryByRole('button', { name: '@mariana' })).not.toBeInTheDocument()
    await userEvent.type(screen.getByLabelText('Write a comment'), 'Please check')
    await userEvent.click(screen.getByRole('button', { name: '@rui' }))
    expect(screen.getByLabelText('Write a comment')).toHaveValue('Please check @rui ')
    await userEvent.click(screen.getByRole('button', { name: 'Comment' }))
    await screen.findByText('Discussion (2)')
    expect(api.calls.find((c) => c.key === 'POST /api/requests/42/comments/')?.body).toEqual({ body: 'Please check @rui' })
  })
})
