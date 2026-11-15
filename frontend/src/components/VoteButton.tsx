import { useState } from 'react'
import { setVote } from '../api/requests'

type Props = {
  id: number
  title: string
  votes: number
  voted: boolean
  layout?: 'stacked' | 'inline'
  onChange: (state: { votes: number; voted: boolean }) => void
}

/** Botão de voto: um voto por utilizador; clicar outra vez retira-o. */
export default function VoteButton({ id, title, votes, voted, layout = 'stacked', onChange }: Props) {
  const [busy, setBusy] = useState(false)
  const [failed, setFailed] = useState(false)

  async function toggle() {
    setBusy(true)
    setFailed(false)
    try {
      onChange(await setVote(id, !voted))
    } catch {
      setFailed(true)
    } finally {
      setBusy(false)
    }
  }

  const label = voted ? `Remove vote from ${title}` : `Vote for ${title}`
  if (layout === 'inline') {
    return (
      <button type="button" className={`btn ${voted ? 'btn-voted' : ''}`} aria-label={label} aria-pressed={voted} disabled={busy} onClick={toggle}>
        {voted ? '✓ Voted' : '▲ Vote'} · {votes}
        {failed && <span className="vote-error"> · try again</span>}
      </button>
    )
  }
  return (
    <div className="vote">
      <span className="vote-count">{votes}</span>
      <button type="button" className={`btn btn-small ${voted ? 'btn-voted' : ''}`} aria-label={label} aria-pressed={voted} disabled={busy} onClick={toggle}>
        {voted ? 'Voted' : 'Vote'}
      </button>
      {failed && <span className="vote-error">Try again</span>}
    </div>
  )
}
