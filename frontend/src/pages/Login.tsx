import { useState, type FormEvent } from 'react'
import { messageOf } from '../api/client'
import { useAuth } from '../auth/AuthContext'

export default function Login() {
  const { signIn } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await signIn(username.trim(), password)
    } catch (caught) {
      setError(messageOf(caught, 'Could not sign in. Check that the API is running and try again.'))
      setBusy(false)
    }
  }

  return (
    <main className="login">
      <form className="login-card" onSubmit={submit} noValidate>
        <h1 className="brand">FeatureHub</h1>
        <p className="muted">Sign in to your workspace.</p>
        <label className="field">
          <span className="field-label">Username</span>
          <input className="input" autoComplete="username" autoFocus value={username} onChange={(event) => setUsername(event.target.value)} />
        </label>
        <label className="field">
          <span className="field-label">Password</span>
          <input className="input" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} />
        </label>
        {error && (
          <p className="banner banner-error" role="alert">
            {error}
          </p>
        )}
        <button className="btn btn-primary" disabled={busy}>
          Sign in
        </button>
      </form>
    </main>
  )
}
