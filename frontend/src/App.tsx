import { useEffect, useState } from 'react'
import { fetchHealth, type Health } from './api/health'

type State = { kind: 'loading' } | { kind: 'ready'; health: Health } | { kind: 'unavailable' }

function statusText(state: State): string {
  switch (state.kind) {
    case 'loading':
      return 'A verificar…'
    case 'unavailable':
      return 'API indisponível'
    case 'ready':
      return `API: ${state.health.status} · DB: ${state.health.db}`
  }
}

export default function App() {
  const [state, setState] = useState<State>({ kind: 'loading' })

  useEffect(() => {
    const controller = new AbortController()
    fetchHealth(controller.signal)
      .then((health) => setState({ kind: 'ready', health }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: 'unavailable' })
      })
    return () => controller.abort()
  }, [])

  return (
    <main className="app">
      <h1>FeatureHub</h1>
      <p className={`status status-${state.kind === 'ready' ? state.health.status : state.kind}`}>
        {statusText(state)}
      </p>
    </main>
  )
}
