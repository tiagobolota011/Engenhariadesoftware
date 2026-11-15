import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { AuthContext } from '../auth/AuthContext'
import type { User } from '../api/types'
import { mariana, mockApi, page, requestItem, rui } from '../test/mockApi'
import MyRequests from './MyRequests'
import Prioritization from './Prioritization'
import RequestDetail from './RequestDetail'
import RequestsList from './RequestsList'
import SubmitRequest from './SubmitRequest'

function renderAt(path: string, user: unknown = mariana) {
  return render(
    <AuthContext.Provider value={{ user: user as User, signIn: async () => {}, signOut: async () => {} }}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/requests" element={<RequestsList />} />
          <Route path="/requests/new" element={<SubmitRequest />} />
          <Route path="/requests/:id" element={<RequestDetail />} />
          <Route path="/my-requests" element={<MyRequests />} />
          <Route path="/prioritization" element={<Prioritization />} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

const categories = { 'GET /api/categories/': { body: [{ id: 4, name: 'Ordering' }] } }

describe('Feature Requests list', () => {
  it('lists requests with votes, tags, date and status', async () => {
    mockApi({ ...categories, 'GET /api/requests/': { body: page([requestItem()]) } })
    renderAt('/requests')
    const row = (await screen.findByText('Schedule an order in advance')).closest('li')!
    expect(row).toHaveTextContent('12')
    expect(row).toHaveTextContent('Ordering · #scheduling #mobile · 2 Oct 2026')
    expect(within(row).getByText('Under review')).toBeInTheDocument()
    expect(screen.getByText('1 request · sorted by most votes')).toBeInTheDocument()
  })

  it('shows an empty state instead of a blank page', async () => {
    mockApi({ ...categories, 'GET /api/requests/': { body: page([]) } })
    renderAt('/requests')
    expect(await screen.findByText('No requests yet. Be the first to suggest one.')).toBeInTheDocument()
  })

  it('says so when the list cannot be loaded', async () => {
    mockApi({ ...categories, 'GET /api/requests/': { status: 500, body: {} } })
    renderAt('/requests')
    expect(await screen.findByRole('alert')).toHaveTextContent('could not be loaded')
  })

  it('votes and updates the count', async () => {
    const api = mockApi({
      ...categories,
      'GET /api/requests/': { body: page([requestItem()]) },
      'POST /api/requests/42/vote/': { body: { votes: 13, voted: true } },
    })
    renderAt('/requests')
    await userEvent.click(await screen.findByRole('button', { name: 'Vote for Schedule an order in advance' }))
    expect(await screen.findByRole('button', { name: 'Remove vote from Schedule an order in advance' })).toBeInTheDocument()
    expect(screen.getByText('13')).toBeInTheDocument()
    expect(api.count('POST /api/requests/42/vote/')).toBe(1)
  })

  it('sends the chosen filters to the API', async () => {
    const api = mockApi({ ...categories, 'GET /api/requests/': { body: page([]) } })
    renderAt('/requests')
    await userEvent.selectOptions(await screen.findByLabelText('Status'), 'planned')
    await screen.findByText('No requests match these filters.')
    expect(api.calls.at(-1)!.url.searchParams.get('status')).toBe('planned')
  })
})

describe('Submit a feature request', () => {
  it('marks the fields the server rejects', async () => {
    mockApi({
      ...categories,
      'GET /api/requests/similar/': { body: [] },
      'POST /api/requests/': {
        status: 400,
        body: { description: ['This field is required.'], category: ['This field is required.'] },
      },
    })
    renderAt('/requests/new')
    await userEvent.type(await screen.findByLabelText('Title *'), 'Dark mode')
    await userEvent.click(screen.getByRole('button', { name: 'Submit request' }))
    expect(await screen.findAllByText('This field is required.')).toHaveLength(2)
    expect(screen.getByLabelText('Description *')).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByLabelText('Title *')).not.toHaveAttribute('aria-invalid', 'true')
  })

  it('offers similar requests to vote on instead', async () => {
    mockApi({
      ...categories,
      'GET /api/requests/similar/': { body: [requestItem()] },
    })
    renderAt('/requests/new')
    await userEvent.type(await screen.findByLabelText('Title *'), 'Schedule my order')
    expect(await screen.findByText('Similar requests (1)')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Vote instead' })).toBeInTheDocument()
  })

  it('submits and confirms in My Requests', async () => {
    const api = mockApi({
      ...categories,
      'GET /api/requests/similar/': { body: [] },
      'POST /api/requests/': { status: 201, body: requestItem({ id: 7 }) },
      'GET /api/requests/': { body: page([requestItem({ id: 7, my_role: 'created' })]) },
      'GET /api/roadmap/public/': { body: { planned: [], in_progress: [], released: [] } },
    })
    renderAt('/requests/new')
    await userEvent.type(await screen.findByLabelText('Title *'), 'Dark mode')
    await userEvent.type(screen.getByLabelText('Description *'), 'Easier at night.')
    await userEvent.selectOptions(screen.getByLabelText('Category *'), '4')
    await userEvent.type(screen.getByLabelText('Tags'), 'theme, #night')
    await userEvent.click(screen.getByRole('button', { name: 'Submit request' }))
    expect(await screen.findByRole('status')).toHaveTextContent(
      'Thanks, Mariana! Your request was submitted. You can follow it in My Requests.',
    )
    expect(api.calls.find((c) => c.key === 'POST /api/requests/')?.body).toEqual({
      title: 'Dark mode',
      description: 'Easier at night.',
      category: 4,
      tags: ['theme', '#night'],
      importance: '',
    })
  })
})

const detail = (over: Record<string, unknown> = {}) =>
  requestItem({
    description: 'Choose a delivery date and time.',
    importance: '',
    version: 2,
    comments: [
      { id: 1, author_name: 'Mariana Costa', author_role: 'Customer', body: 'Saturday morning.', is_decision: false, created_at: '2026-10-09T09:00:00+00:00' },
    ],
    versions: [
      { number: 2, actor_name: 'Rui Almeida', summary: 'Status → Under review', created_at: '2026-10-06T09:00:00+00:00' },
      { number: 1, actor_name: 'Pedro Nunes', summary: 'Request created', created_at: '2026-10-02T09:00:00+00:00' },
    ],
    assessment: null,
    can_assess: false,
    next_statuses: [],
    ...over,
  })

describe('Request detail', () => {
  it('shows discussion and history, and hides the assessment from customers', async () => {
    mockApi({ 'GET /api/requests/42/': { body: detail() } })
    renderAt('/requests/42')
    expect(await screen.findByRole('heading', { name: 'Schedule an order in advance' })).toBeInTheDocument()
    expect(screen.getByText('Discussion (1)')).toBeInTheDocument()
    expect(screen.getByText('Saturday morning.')).toBeInTheDocument()
    expect(screen.getByText('Request created')).toBeInTheDocument()
    expect(screen.queryByText(/Assessment/)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Mark as decision' })).not.toBeInTheDocument()
  })

  it('lets the product owner save an assessment with the version seen', async () => {
    const po = detail({
      assessment: { impact: null, effort: null },
      can_assess: true,
      next_statuses: [{ value: 'approved', label: 'Approved' }, { value: 'rejected', label: 'Rejected' }],
    })
    const api = mockApi({
      'GET /api/requests/42/': { body: po },
      'PATCH /api/requests/42/assessment/': { body: { ...po, status: 'approved', status_label: 'Approved', version: 3 } },
    })
    renderAt('/requests/42', rui)
    await userEvent.selectOptions(await screen.findByLabelText('Impact (1–5)'), '5')
    await userEvent.type(screen.getByLabelText('Effort (points)'), '8')
    await userEvent.selectOptions(screen.getByLabelText('Change status'), 'approved')
    await userEvent.click(screen.getByRole('button', { name: 'Save assessment' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Assessment saved.')
    expect(api.calls.find((c) => c.key === 'PATCH /api/requests/42/assessment/')?.body).toEqual({
      version: 2,
      impact: 5,
      effort: 8,
      status: 'approved',
    })
  })

  it('explains a version conflict instead of overwriting', async () => {
    const po = detail({ assessment: { impact: 3, effort: 2 }, can_assess: true })
    mockApi({
      'GET /api/requests/42/': { body: po },
      'PATCH /api/requests/42/assessment/': {
        status: 412,
        body: { detail: 'This request was changed by someone else. Reload and try again.', version: 3 },
      },
    })
    renderAt('/requests/42', rui)
    await userEvent.click(await screen.findByRole('button', { name: 'Save assessment' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('changed by someone else')
  })

  it('posts a comment', async () => {
    const api = mockApi({
      'GET /api/requests/42/': { body: detail() },
      'POST /api/requests/42/comments/': {
        status: 201,
        body: { id: 2, author_name: 'Mariana Costa', author_role: 'Customer', body: 'Card is fine.', is_decision: false, created_at: '2026-10-24T09:00:00+00:00' },
      },
    })
    renderAt('/requests/42')
    await userEvent.type(await screen.findByLabelText('Write a comment'), 'Card is fine.')
    await userEvent.click(screen.getByRole('button', { name: 'Comment' }))
    expect(await screen.findByText('Card is fine.')).toBeInTheDocument()
    expect(screen.getByText('Discussion (2)')).toBeInTheDocument()
    expect(api.count('POST /api/requests/42/comments/')).toBe(1)
  })

  it('shows not found for a request outside the workspace', async () => {
    mockApi({ 'GET /api/requests/42/': { status: 404, body: { detail: 'Not found.' } } })
    renderAt('/requests/42')
    expect(await screen.findByText('This request does not exist or is not in your workspace.')).toBeInTheDocument()
  })
})

describe('My Requests', () => {
  it('lists my requests with my role and the public roadmap', async () => {
    const api = mockApi({
      'GET /api/requests/': { body: page([requestItem({ my_role: 'voted', votes: 13 })]) },
      'GET /api/roadmap/public/': {
        body: { planned: [{ id: 9, title: 'Export order history to PDF', category: 'Account' }], in_progress: [], released: [] },
      },
    })
    renderAt('/my-requests')
    const row = (await screen.findByText('Schedule an order in advance')).closest('tr')!
    expect(row).toHaveTextContent('Voted')
    expect(row).toHaveTextContent('13')
    expect(row).toHaveTextContent('9 Oct 2026')
    expect(screen.getByText('Planned · 1')).toBeInTheDocument()
    expect(screen.getByText('Export order history to PDF')).toBeInTheDocument()
    expect(api.calls.find((c) => c.key === 'GET /api/requests/')!.url.searchParams.get('mine')).toBe('1')
  })
})

describe('Prioritization', () => {
  const rows = [
    { id: 1, key: 'REQ-001', title: 'Schedule an order in advance', category: 'Ordering', votes: 13, impact: 5, effort: 8, score: 8.1, manual: false, manual_rank: null, override_reason: '' },
    { id: 2, key: 'REQ-002', title: 'Recurring weekly orders', category: 'Ordering', votes: 4, impact: 2, effort: 3, score: 2.7, manual: true, manual_rank: 1, override_reason: 'contract commitment' },
    { id: 3, key: 'REQ-003', title: 'Edit order after checkout', category: 'Ordering', votes: 7, impact: null, effort: null, score: null, manual: false, manual_rank: null, override_reason: '' },
  ]
  const suggestion = {
    basis: 'Calculated by FeatureHub from votes, impact and effort (score = votes × impact ÷ effort). No external AI service is used.',
    items: [{ id: 1, key: 'REQ-001', title: 'Schedule an order in advance', reason: 'Score 8.1: 13 votes × impact 5 ÷ effort 8 pts.' }],
  }
  const routes = {
    ...categories,
    'GET /api/prioritization/': { body: rows },
    'GET /api/prioritization/suggestion/': { body: suggestion },
  }

  it('shows score, manual override and missing estimate', async () => {
    mockApi(routes)
    renderAt('/prioritization', rui)
    const first = (await screen.findByText('Schedule an order in advance', { selector: 'a' })).closest('tr')!
    expect(first).toHaveTextContent('8.1')
    expect(screen.getByText('Moved manually · contract commitment')).toBeInTheDocument()
    expect(screen.getByText('Missing estimate')).toBeInTheDocument()
    expect(screen.getByText(/No external AI service is used/)).toBeInTheDocument()
    expect(screen.getByText('Score 8.1: 13 votes × impact 5 ÷ effort 8 pts.')).toBeInTheDocument()
  })

  it('asks for a reason before moving a request', async () => {
    const api = mockApi({ ...routes, 'POST /api/prioritization/reorder/': { body: { id: 3, position: 1 } } })
    renderAt('/prioritization', rui)
    await userEvent.click(await screen.findByRole('button', { name: 'Move Edit order after checkout up' }))
    await userEvent.type(screen.getByLabelText('Reason for moving'), 'Legal deadline')
    await userEvent.click(screen.getByRole('button', { name: 'Move' }))
    await screen.findByText('Schedule an order in advance', { selector: 'a' })
    expect(api.calls.find((c) => c.key === 'POST /api/prioritization/reorder/')?.body).toEqual({
      request: 3,
      position: 1,
      reason: 'Legal deadline',
    })
  })

  it('accepts the suggestion', async () => {
    const api = mockApi({ ...routes, 'POST /api/prioritization/suggestion/accept/': { status: 204 } })
    renderAt('/prioritization', rui)
    await userEvent.click(await screen.findByRole('button', { name: 'Accept' }))
    await screen.findByText('Suggested order applied.')
    expect(api.count('POST /api/prioritization/suggestion/accept/')).toBe(1)
  })

  it('refuses other roles', async () => {
    mockApi(routes)
    renderAt('/prioritization', mariana)
    expect(await screen.findByText('Only the Product Owner can prioritise requests.')).toBeInTheDocument()
  })
})
