import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { listCategories, listRequests } from '../api/requests'
import type { Category, RequestSummary } from '../api/types'
import Badge from '../components/Badge'
import VoteButton from '../components/VoteButton'
import { formatDate, plural } from '../format'

const STATUSES = [
  ['submitted', 'Submitted'],
  ['under_review', 'Under review'],
  ['approved', 'Approved'],
  ['rejected', 'Rejected'],
  ['planned', 'Planned'],
  ['in_progress', 'In progress'],
  ['released', 'Released'],
]
const DATES = [
  ['7d', 'Last 7 days'],
  ['30d', 'Last 30 days'],
  ['90d', 'Last 90 days'],
]

/** WF-01 · Request Portal: lista, pesquisa, filtros e voto. */
export default function RequestsList() {
  const [params] = useSearchParams()
  const fromUrl = params.get('search') ?? ''
  const [typed, setTyped] = useState(fromUrl)
  const [search, setSearch] = useState(fromUrl)
  const [status, setStatus] = useState('')
  const [category, setCategory] = useState('')
  const [date, setDate] = useState('')
  const [categories, setCategories] = useState<Category[]>([])
  const [items, setItems] = useState<RequestSummary[] | null>(null)
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    listCategories()
      .then(setCategories)
      .catch(() => setCategories([]))
  }, [])

  // A pesquisa do topo chega pelo URL.
  useEffect(() => {
    setTyped(fromUrl)
    setSearch(fromUrl)
  }, [fromUrl])

  // Espera que a pessoa pare de escrever antes de pesquisar.
  useEffect(() => {
    const timer = setTimeout(() => setSearch(typed.trim()), 300)
    return () => clearTimeout(timer)
  }, [typed])

  useEffect(() => {
    let current = true
    setFailed(false)
    listRequests({ search, status, category, date })
      .then((data) => {
        if (!current) return
        setItems(data.results)
        setCount(data.count)
        setHasMore(data.next !== null)
        setPage(1)
      })
      .catch(() => current && setFailed(true))
    return () => {
      current = false
    }
  }, [search, status, category, date])

  async function loadMore() {
    try {
      const data = await listRequests({ search, status, category, date, page: page + 1 })
      setItems((previous) => [...(previous ?? []), ...data.results])
      setHasMore(data.next !== null)
      setPage(page + 1)
    } catch {
      setFailed(true)
    }
  }

  const filtered = Boolean(search || status || category || date)

  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="page-title">Feature Requests</h1>
          <p className="page-subtitle">Browse ideas, vote for the ones you want, or suggest a new one.</p>
        </div>
        <Link to="/requests/new" className="btn btn-primary">
          + New Request
        </Link>
      </div>

      <div className="filters">
        <input className="input grow" aria-label="Search requests" placeholder="Search requests…" value={typed} onChange={(event) => setTyped(event.target.value)} />
        <select className="select" aria-label="Status" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">Status: All</option>
          {STATUSES.map(([value, label]) => (
            <option key={value} value={value}>
              Status: {label}
            </option>
          ))}
        </select>
        <select className="select" aria-label="Category" value={category} onChange={(event) => setCategory(event.target.value)}>
          <option value="">Category: All</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              Category: {c.name}
            </option>
          ))}
        </select>
        <select className="select" aria-label="Date" value={date} onChange={(event) => setDate(event.target.value)}>
          <option value="">Date: Any time</option>
          {DATES.map(([value, label]) => (
            <option key={value} value={value}>
              Date: {label}
            </option>
          ))}
        </select>
      </div>

      {failed && (
        <p className="banner banner-error" role="alert">
          The requests could not be loaded. Check your connection and reload the page.
        </p>
      )}
      {!failed && items === null && <p className="muted">Loading requests…</p>}
      {!failed && items !== null && items.length === 0 && (
        <p className="empty">
          {filtered ? 'No requests match these filters.' : 'No requests yet. Be the first to suggest one.'}
        </p>
      )}
      {!failed && items !== null && items.length > 0 && (
        <>
          <p className="list-count">{plural(count, 'request')} · sorted by most votes</p>
          <ul className="request-list">
            {items.map((item) => (
              <li key={item.id} className="request-row">
                <VoteButton
                  id={item.id}
                  title={item.title}
                  votes={item.votes}
                  voted={item.voted}
                  onChange={(state) => setItems((all) => (all ?? []).map((r) => (r.id === item.id ? { ...r, ...state } : r)))}
                />
                <div className="grow">
                  <Link to={`/requests/${item.id}`} className="request-title">
                    {item.title}
                  </Link>
                  <div className="request-meta">
                    {[item.category.name, item.tags.map((tag) => `#${tag}`).join(' '), formatDate(item.created_at)].filter(Boolean).join(' · ')}
                  </div>
                </div>
                <Badge>{item.status_label}</Badge>
              </li>
            ))}
          </ul>
          {hasMore && (
            <button type="button" className="btn load-more" onClick={loadMore}>
              Load more
            </button>
          )}
        </>
      )}
    </>
  )
}
