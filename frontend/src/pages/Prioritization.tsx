import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { messageOf } from '../api/client'
import { acceptSuggestion, getSuggestion, listPriorities, reorder } from '../api/prioritization'
import { listCategories } from '../api/requests'
import type { Category, PriorityRow, Suggestion } from '../api/types'
import { useUser } from '../auth/AuthContext'
import Badge from '../components/Badge'
import { plural } from '../format'

/** WF-05 · Prioritization: tabela com score, ordem manual e sugestão calculada. */
export default function Prioritization() {
  const user = useUser()
  const allowed = user.role === 'product_owner'
  const [category, setCategory] = useState('')
  const [categories, setCategories] = useState<Category[]>([])
  const [rows, setRows] = useState<PriorityRow[] | null>(null)
  const [suggestion, setSuggestion] = useState<Suggestion | null>(null)
  const [showSuggestion, setShowSuggestion] = useState(true)
  const [moving, setMoving] = useState<{ row: PriorityRow; position: number } | null>(null)
  const [reason, setReason] = useState('')
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try {
      const [table, suggested] = await Promise.all([listPriorities(category), getSuggestion(category)])
      setRows(table)
      setSuggestion(suggested)
    } catch (caught) {
      setError(messageOf(caught, 'The prioritisation table could not be loaded. Reload the page.'))
    }
  }, [category])

  useEffect(() => {
    if (!allowed) return
    listCategories()
      .then(setCategories)
      .catch(() => setCategories([]))
  }, [allowed])

  useEffect(() => {
    if (allowed) void load()
  }, [allowed, load])

  if (!allowed) return <p className="empty">Only the Product Owner can prioritise requests.</p>

  async function move(event: FormEvent) {
    event.preventDefault()
    if (!moving || !reason.trim()) return
    setError('')
    setNotice('')
    try {
      await reorder(moving.row.id, moving.position, reason.trim())
      setMoving(null)
      setReason('')
      await load()
    } catch (caught) {
      setError(messageOf(caught, 'The request was not moved. Try again.'))
    }
  }

  async function accept() {
    setError('')
    try {
      await acceptSuggestion(category)
      await load()
      setNotice('Suggested order applied.')
    } catch (caught) {
      setError(messageOf(caught, 'The suggestion could not be applied. Try again.'))
    }
  }

  const overrides = rows?.filter((row) => row.manual).length ?? 0

  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="page-title">Prioritization</h1>
          <p className="page-subtitle">Score = votes × impact ÷ effort</p>
        </div>
        <select className="select" aria-label="Category" value={category} onChange={(event) => setCategory(event.target.value)}>
          <option value="">Category: All</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              Category: {c.name}
            </option>
          ))}
        </select>
      </div>
      {error && (
        <p className="banner banner-error" role="alert">
          {error}
        </p>
      )}
      {notice && (
        <p className="banner banner-success" role="status">
          {notice}
        </p>
      )}
      {rows === null && !error && <p className="muted">Loading…</p>}
      {rows !== null && rows.length === 0 && <p className="empty">No open requests to prioritise in this category.</p>}
      {rows !== null && rows.length > 0 && (
        <div className="two-columns">
          <div>
            <table className="table">
              <thead>
                <tr>
                  <th aria-label="Reorder" />
                  <th>Request</th>
                  <th>Votes</th>
                  <th>Impact</th>
                  <th>Effort</th>
                  <th>Score</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, index) => (
                  <tr key={row.id} className={row.manual ? 'row-manual' : undefined}>
                    <td className="reorder">
                      <button type="button" className="icon-button" aria-label={`Move ${row.title} up`} disabled={index === 0} onClick={() => setMoving({ row, position: index - 1 })}>
                        ▲
                      </button>
                      <button type="button" className="icon-button" aria-label={`Move ${row.title} down`} disabled={index === rows.length - 1} onClick={() => setMoving({ row, position: index + 1 })}>
                        ▼
                      </button>
                    </td>
                    <td>
                      <Link to={`/requests/${row.id}`} className="request-title">
                        {row.title}
                      </Link>{' '}
                      {row.manual && (
                        <Badge variant="dashed">
                          <span aria-hidden="true">↑ </span>
                          <span>Moved manually · {row.override_reason}</span>
                        </Badge>
                      )}
                      {row.score === null && <span className="muted">Missing estimate</span>}
                    </td>
                    <td>{row.votes}</td>
                    <td>{row.impact ?? '—'}</td>
                    <td>{row.effort === null ? '—' : `${row.effort} pts`}</td>
                    <td>
                      <strong>{row.score === null ? '—' : row.score.toFixed(1)}</strong>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {moving && (
              <form className="move-form" onSubmit={move}>
                <span>
                  Move <strong>{moving.row.title}</strong> to position {moving.position + 1}.
                </span>
                <input className="input grow" aria-label="Reason for moving" placeholder="Why? e.g. contract commitment" autoFocus value={reason} onChange={(event) => setReason(event.target.value)} />
                <button className="btn btn-primary" disabled={!reason.trim()}>
                  Move
                </button>
                <button type="button" className="btn" onClick={() => setMoving(null)}>
                  Cancel
                </button>
              </form>
            )}
            <p className="list-count">
              Ranked by score · {plural(overrides, 'manual override')} · use ▲ ▼ to reorder · open a request to set impact and effort
            </p>
          </div>

          {suggestion && showSuggestion && (
            <aside className="panel">
              <h2 className="panel-title">AI Suggestion</h2>
              <p className="muted">{suggestion.basis}</p>
              <ol className="suggestion">
                {suggestion.items.map((entry, index) => (
                  <li key={entry.id} className="card">
                    <div className="card-title">
                      {index + 1}. {entry.title}
                    </div>
                    <div className="request-meta">{entry.reason}</div>
                  </li>
                ))}
              </ol>
              <div className="actions">
                <button type="button" className="btn btn-primary grow" onClick={accept}>
                  Accept
                </button>
                <button type="button" className="btn grow" onClick={() => setShowSuggestion(false)}>
                  Override
                </button>
              </div>
            </aside>
          )}
        </div>
      )}
    </>
  )
}
