import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { listRequests, publicRoadmap } from '../api/requests'
import type { PublicRoadmap, RequestSummary } from '../api/types'
import Badge from '../components/Badge'
import { formatDate } from '../format'

const COLUMNS = [
  ['planned', 'Planned'],
  ['in_progress', 'In progress'],
  ['released', 'Released'],
] as const

/** WF-04 · My Requests: os pedidos que criei ou votei e o roadmap público. */
export default function MyRequests() {
  const flash = (useLocation().state as { flash?: string } | null)?.flash
  const [items, setItems] = useState<RequestSummary[] | null>(null)
  const [roadmap, setRoadmap] = useState<PublicRoadmap | null>(null)
  const [total, setTotal] = useState(0)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    Promise.all([listRequests({ mine: true }), publicRoadmap()])
      .then(([mine, columns]) => {
        setItems(mine.results)
        setTotal(mine.count)
        setRoadmap(columns)
      })
      .catch(() => setFailed(true))
  }, [])

  return (
    <>
      <h1 className="page-title">My Requests</h1>
      {flash && (
        <p className="banner banner-success" role="status">
          {flash}
        </p>
      )}
      {failed && (
        <p className="banner banner-error" role="alert">
          Your requests could not be loaded. Reload the page to try again.
        </p>
      )}
      {!failed && items === null && <p className="muted">Loading your requests…</p>}
      {items !== null && (
        <>
          <div className="tabs">
            <span className="tab tab-active">My Requests ({total}) — created or voted</span>
            <a className="tab" href="#public-roadmap">
              Public Roadmap
            </a>
          </div>
          {items.length === 0 ? (
            <p className="empty">
              You have not created or voted on any request yet. <Link to="/requests">Browse requests</Link> or{' '}
              <Link to="/requests/new">suggest one</Link>.
            </p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Request</th>
                  <th>My role</th>
                  <th>Status</th>
                  <th>Votes</th>
                  <th>Last update</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <Link to={`/requests/${item.id}`} className="request-title">
                        {item.title}
                      </Link>
                    </td>
                    <td>{item.my_role === 'created' ? 'Created' : 'Voted'}</td>
                    <td>
                      <Badge>{item.status_label}</Badge>
                    </td>
                    <td>{item.votes}</td>
                    <td>{formatDate(item.updated_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {total > items.length && <p className="list-count">Showing the {items.length} most voted of {total}.</p>}
        </>
      )}

      {roadmap && (
        <section id="public-roadmap">
          <h2 className="section-title">
            Public Roadmap <span className="muted">Read-only · no personal data shown</span>
          </h2>
          <div className="board">
            {COLUMNS.map(([key, label]) => (
              <div key={key} className="board-column">
                <h3 className="board-title">
                  {label} · {roadmap[key].length}
                </h3>
                {roadmap[key].map((entry) => (
                  <div key={entry.id} className="card">
                    <div className="card-title">{entry.title}</div>
                    <div className="request-meta">{entry.category}</div>
                  </div>
                ))}
                {roadmap[key].length === 0 && <p className="muted">Nothing here yet.</p>}
              </div>
            ))}
          </div>
        </section>
      )}
    </>
  )
}
