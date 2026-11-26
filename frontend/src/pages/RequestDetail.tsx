import { useCallback, useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError, messageOf } from '../api/client'
import { listMembers } from '../api/notifications'
import { addComment, getRequest, markDecision, removeDecision, saveAssessment } from '../api/requests'
import type { RequestDetail as Detail, Member, RequestStatus } from '../api/types'
import { useUser } from '../auth/AuthContext'
import Badge from '../components/Badge'
import VoteButton from '../components/VoteButton'
import { formatDate } from '../format'

const STEP_OF: Record<RequestStatus, number> = {
  submitted: 0,
  under_review: 1,
  approved: 2,
  rejected: 2,
  planned: 3,
  in_progress: 4,
  released: 5,
}

function steps(status: RequestStatus): string[] {
  const outcome = status === 'rejected' ? 'Rejected' : STEP_OF[status] >= 2 ? 'Approved' : 'Approved / Rejected'
  return ['Submitted', 'Under review', outcome, 'Planned', 'In progress', 'Released']
}

// Mesma regra do backend (apps/collaboration/notifications.py).
const MENTION = /(?<![\w@])@([\w.+-]*\w)/g

/** Destaca as menções a membros do workspace no texto de um comentário. */
function withMentions(body: string, usernames: Set<string>): ReactNode[] {
  const parts: ReactNode[] = []
  let last = 0
  for (const match of body.matchAll(MENTION)) {
    if (!usernames.has(match[1].toLowerCase())) continue
    parts.push(body.slice(last, match.index))
    parts.push(
      <span key={match.index} className="mention">
        {match[0]}
      </span>,
    )
    last = match.index + match[0].length
  }
  parts.push(body.slice(last))
  return parts
}

/** WF-03 · Request Detail: estados, discussão, avaliação do PO e histórico. */
export default function RequestDetail() {
  const { id = '' } = useParams()
  const [item, setItem] = useState<Detail | null>(null)
  const [problem, setProblem] = useState<'missing' | 'failed' | null>(null)
  const [text, setText] = useState('')
  const [commentError, setCommentError] = useState('')
  const [impact, setImpact] = useState('')
  const [effort, setEffort] = useState('')
  const [status, setStatus] = useState<string>('')
  const [saved, setSaved] = useState('')
  const [saveError, setSaveError] = useState('')
  const me = useUser()
  const [members, setMembers] = useState<Member[]>([])

  useEffect(() => {
    // Sem a lista de membros só se perde a sugestão de menções; o ecrã continua a funcionar.
    listMembers()
      .then(setMembers)
      .catch(() => setMembers([]))
  }, [])

  const show = useCallback((data: Detail) => {
    setItem(data)
    setImpact(data.assessment?.impact?.toString() ?? '')
    setEffort(data.assessment?.effort?.toString() ?? '')
    setStatus(data.status)
  }, [])

  const load = useCallback(
    () =>
      getRequest(id)
        .then(show)
        .catch((caught) => setProblem(caught instanceof ApiError && caught.status === 404 ? 'missing' : 'failed')),
    [id, show],
  )

  useEffect(() => {
    setItem(null)
    setProblem(null)
    void load()
  }, [load])

  if (problem === 'missing') return <p className="empty">This request does not exist or is not in your workspace.</p>
  if (problem === 'failed') {
    return (
      <p className="banner banner-error" role="alert">
        This request could not be loaded. Reload the page to try again.
      </p>
    )
  }
  if (!item) return <p className="muted">Loading request…</p>

  const usernames = new Set(members.map((m) => m.username.toLowerCase()))
  const teammates = members.filter((m) => m.username !== me.username)
  const mention = (username: string) =>
    setText((now) => `${now}${now && !now.endsWith(' ') ? ' ' : ''}@${username} `)
  const current = STEP_OF[item.status]

  async function comment(event: FormEvent) {
    event.preventDefault()
    if (!item || !text.trim()) return
    setCommentError('')
    try {
      const created = await addComment(item.id, text.trim())
      setItem((now) => (now ? { ...now, comments: [...now.comments, created] } : now))
      setText('')
    } catch {
      setCommentError('Your comment was not posted. Try again.')
    }
  }

  async function decide(commentId: number, marked: boolean) {
    if (!item) return
    setSaved('')
    setSaveError('')
    try {
      await (marked ? markDecision : removeDecision)(item.id, commentId)
      await load()
    } catch (caught) {
      setSaveError(messageOf(caught, 'The decision could not be recorded. Try again.'))
    }
  }

  async function assess(event: FormEvent) {
    event.preventDefault()
    if (!item) return
    setSaved('')
    setSaveError('')
    try {
      show(
        await saveAssessment(item.id, {
          version: item.version,
          impact: impact ? Number(impact) : null,
          effort: effort ? Number(effort) : null,
          status,
        }),
      )
      setSaved('Assessment saved.')
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 400) {
        setSaveError(Object.values(caught.fieldErrors()).join(' ') || 'Check the values and try again.')
      } else {
        setSaveError(messageOf(caught, 'The assessment could not be saved. Try again.'))
        // 412: outra pessoa alterou o pedido entretanto. Nada foi escrito por cima;
        // mostra-se a versão atual para o PO a rever antes de guardar outra vez.
        if (caught instanceof ApiError && caught.status === 412) await load()
      }
    }
  }

  return (
    <>
      <div className="page-head">
        <div>
          <p className="breadcrumb">
            <Link to="/requests">Requests</Link> / #{item.key}
          </p>
          <div className="title-line">
            <h1 className="page-title">{item.title}</h1>
            <Badge>{item.status_label}</Badge>
          </div>
          <p className="request-meta">
            {item.category.name} ·{' '}
            {item.tags.map((tag) => (
              <span key={tag} className="chip">
                {tag}
              </span>
            ))}{' '}
            · by {item.author_name} · {formatDate(item.created_at)}
          </p>
        </div>
        <VoteButton id={item.id} title={item.title} votes={item.votes} voted={item.voted} layout="inline" onChange={(state) => setItem((now) => (now ? { ...now, ...state } : now))} />
      </div>

      <ol className="stepper" aria-label="Request status">
        {steps(item.status).map((label, index) => (
          <li key={label} className={index <= current ? 'step step-done' : 'step'} aria-current={index === current ? 'step' : undefined}>
            <span className="step-dot" aria-hidden="true" />
            {label}
          </li>
        ))}
      </ol>

      <div className="two-columns">
        <div>
          <h2 className="section-label">Description</h2>
          <p className="prose">{item.description}</p>
          {item.importance && (
            <>
              <h2 className="section-label">Why this matters</h2>
              <p className="prose">{item.importance}</p>
            </>
          )}

          <h2 className="section-label">Discussion ({item.comments.length})</h2>
          {item.comments.map((c) => (
            <div key={c.id} className="comment">
              <span className="avatar" aria-hidden="true" />
              <div className={c.is_decision ? 'comment-body comment-decision' : 'comment-body'}>
                <div className="comment-head">
                  <span>
                    <strong>{c.author_name}</strong> · {c.author_role} · {formatDate(c.created_at)}
                  </span>
                  {c.is_decision && <Badge variant="success">✓ Decision</Badge>}
                  {item.can_assess && (
                    <button type="button" className="link-button" onClick={() => decide(c.id, !c.is_decision)}>
                      {c.is_decision ? 'Remove decision' : 'Mark as decision'}
                    </button>
                  )}
                </div>
                <p>{withMentions(c.body, usernames)}</p>
              </div>
            </div>
          ))}
          <form className="comment-form" onSubmit={comment}>
            <input className="input grow" aria-label="Write a comment" placeholder="Write a comment…" value={text} onChange={(event) => setText(event.target.value)} />
            <button className="btn" disabled={!text.trim()}>
              Comment
            </button>
          </form>
          {teammates.length > 0 && (
            <p className="mention-hint">
              Mention a teammate with @username to notify them:
              {teammates.map((m) => (
                <button
                  key={m.username}
                  type="button"
                  className="link-button"
                  title={`${m.name} · ${m.role_label}`}
                  onClick={() => mention(m.username)}
                >
                  @{m.username}
                </button>
              ))}
            </p>
          )}
          {commentError && (
            <p className="banner banner-error" role="alert">
              {commentError}
            </p>
          )}
        </div>

        <aside>
          {item.assessment && (
            <form className="panel" onSubmit={assess}>
              <h2 className="section-label">{item.can_assess ? 'Assessment · Product Owner only' : 'Assessment'}</h2>
              <div className="field-pair">
                <label className="field">
                  <span className="field-label">Impact (1–5)</span>
                  <select className="select" value={impact} disabled={!item.can_assess} onChange={(event) => setImpact(event.target.value)}>
                    <option value="">—</option>
                    {[1, 2, 3, 4, 5].map((n) => (
                      <option key={n} value={n}>
                        {n}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span className="field-label">Effort (points)</span>
                  <input className="input" type="number" min={1} value={effort} disabled={!item.can_assess} onChange={(event) => setEffort(event.target.value)} />
                </label>
              </div>
              {item.can_assess && (
                <>
                  <label className="field">
                    <span className="field-label">Change status</span>
                    <select className="select" value={status} onChange={(event) => setStatus(event.target.value)}>
                      <option value={item.status}>{item.status_label}</option>
                      {item.next_statuses.map((next) => (
                        <option key={next.value} value={next.value}>
                          {next.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <button className="btn btn-primary">Save assessment</button>
                </>
              )}
              {saved && (
                <p className="banner banner-success" role="status">
                  {saved}
                </p>
              )}
            </form>
          )}
          {saveError && (
            <p className="banner banner-error" role="alert">
              {saveError}
            </p>
          )}

          <div className="panel panel-plain">
            <h2 className="section-label">Version history</h2>
            {item.versions.map((v) => (
              <div key={v.number} className="version">
                <div>
                  <strong>v{v.number}</strong> · {formatDate(v.created_at)} · {v.actor_name}
                </div>
                <div className="muted">{v.summary}</div>
              </div>
            ))}
          </div>
        </aside>
      </div>
    </>
  )
}
