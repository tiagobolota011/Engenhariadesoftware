import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { createRequest, listCategories, setVote, similarRequests } from '../api/requests'
import type { Category, RequestSummary } from '../api/types'
import { useUser } from '../auth/AuthContext'
import { plural } from '../format'

const splitTags = (text: string) =>
  text
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean)

/** WF-02 · Submit Request, com o painel "Similar requests" (UC-01). */
export default function SubmitRequest() {
  const user = useUser()
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState('')
  const [tags, setTags] = useState('')
  const [importance, setImportance] = useState('')
  const [categories, setCategories] = useState<Category[]>([])
  const [similar, setSimilar] = useState<RequestSummary[] | null>(null)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [failure, setFailure] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    listCategories()
      .then(setCategories)
      .catch(() => setFailure('The categories could not be loaded. Reload the page.'))
  }, [])

  // Procura pedidos parecidos enquanto o título é escrito.
  useEffect(() => {
    const text = title.trim()
    if (text.length < 3) {
      setSimilar(null)
      return
    }
    let current = true
    const timer = setTimeout(() => {
      similarRequests(text, splitTags(tags))
        .then((found) => current && setSimilar(found))
        .catch(() => current && setSimilar(null))
    }, 300)
    return () => {
      current = false
      clearTimeout(timer)
    }
  }, [title, tags])

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setErrors({})
    setFailure('')
    try {
      await createRequest({
        title: title.trim(),
        description: description.trim(),
        category: category ? Number(category) : null,
        tags: splitTags(tags),
        importance: importance.trim(),
      })
      navigate('/my-requests', {
        state: {
          flash: `Thanks, ${user.name.split(' ')[0]}! Your request was submitted. You can follow it in My Requests.`,
        },
      })
    } catch (caught) {
      const fields = caught instanceof ApiError && caught.status === 400 ? caught.fieldErrors() : {}
      setErrors(fields)
      if (Object.keys(fields).length === 0) {
        setFailure('The request could not be submitted. Nothing was saved; try again.')
      }
      setBusy(false)
    }
  }

  async function voteInstead(item: RequestSummary) {
    try {
      if (!item.voted) await setVote(item.id, true)
      navigate(`/requests/${item.id}`)
    } catch {
      setFailure('Your vote could not be saved. Try again.')
    }
  }

  const invalid = (field: string) => (errors[field] ? { 'aria-invalid': true as const, 'aria-describedby': `${field}-error` } : {})
  const hint = (field: string) =>
    errors[field] && (
      <span className="field-error" id={`${field}-error`}>
        {errors[field]}
      </span>
    )

  return (
    <>
      <p className="breadcrumb">
        <Link to="/requests">Requests</Link> / New request
      </p>
      <h1 className="page-title">Submit a feature request</h1>
      <div className="two-columns">
        <form className="form" onSubmit={submit} noValidate>
          <div className="field">
            <label>
              <span className="field-label">Title *</span>
              <input className="input" value={title} onChange={(event) => setTitle(event.target.value)} {...invalid('title')} />
            </label>
            {hint('title')}
          </div>
          <div className="field">
            <label>
              <span className="field-label">Description *</span>
              <textarea className="input" rows={5} value={description} onChange={(event) => setDescription(event.target.value)} {...invalid('description')} />
            </label>
            {hint('description')}
          </div>
          <div className="field-pair">
            <div className="field">
              <label>
                <span className="field-label">Category *</span>
                <select className="select" value={category} onChange={(event) => setCategory(event.target.value)} {...invalid('category')}>
                  <option value="">Select…</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </label>
              {hint('category')}
            </div>
            <div className="field">
              <label>
                <span className="field-label">Tags</span>
                <input className="input" placeholder="scheduling, mobile" value={tags} onChange={(event) => setTags(event.target.value)} {...invalid('tags')} />
              </label>
              {hint('tags')}
            </div>
          </div>
          <div className="field">
            <label>
              <span className="field-label">Why is this important to you?</span>
              <textarea className="input" rows={3} placeholder="Tell us how this would help you…" value={importance} onChange={(event) => setImportance(event.target.value)} />
            </label>
          </div>
          {failure && (
            <p className="banner banner-error" role="alert">
              {failure}
            </p>
          )}
          <div className="actions">
            <button className="btn btn-primary" disabled={busy}>
              Submit request
            </button>
            <Link to="/requests" className="btn">
              Cancel
            </Link>
          </div>
        </form>

        {similar !== null && (
          <aside className="panel">
            <h2 className="panel-title">Similar requests ({similar.length})</h2>
            {similar.length === 0 ? (
              <p className="muted">No similar request found. Yours looks new.</p>
            ) : (
              <>
                <p className="muted">Matching “{title.trim()}”. Vote instead of creating a duplicate.</p>
                {similar.map((item) => (
                  <div key={item.id} className="card">
                    <Link to={`/requests/${item.id}`} className="card-title">
                      {item.title}
                    </Link>
                    <div className="request-meta">
                      {item.category.name} · {plural(item.votes, 'vote')} · {item.status_label}
                    </div>
                    <button type="button" className="btn btn-small" onClick={() => voteInstead(item)}>
                      Vote instead
                    </button>
                  </div>
                ))}
              </>
            )}
          </aside>
        )}
      </div>
    </>
  )
}
