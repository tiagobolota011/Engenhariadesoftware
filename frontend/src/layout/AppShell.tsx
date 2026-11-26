import { useEffect, useState, type FormEvent } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { NOTIFICATIONS_CHANGED, unreadCount } from '../api/notifications'
import { useAuth, useUser } from '../auth/AuthContext'
import { NAV } from './nav'

export default function AppShell() {
  const user = useUser()
  const { signOut } = useAuth()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [unread, setUnread] = useState(0)
  const { pathname } = useLocation()

  // O contador é relido a cada mudança de ecrã e quando um ecrã marca notificações como lidas.
  useEffect(() => {
    let active = true
    const refresh = () =>
      unreadCount()
        .then((data) => active && setUnread(data.unread))
        .catch(() => undefined)
    void refresh()
    window.addEventListener(NOTIFICATIONS_CHANGED, refresh)
    return () => {
      active = false
      window.removeEventListener(NOTIFICATIONS_CHANGED, refresh)
    }
  }, [pathname])

  function search(event: FormEvent) {
    event.preventDefault()
    navigate(`/requests?search=${encodeURIComponent(query.trim())}`)
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <Link to="/requests" className="brand">
          FeatureHub
        </Link>
        <nav aria-label="Main">
          {NAV.filter((item) => item.roles.includes(user.role)).map((item) => (
            <NavLink key={item.to} to={item.to} className="nav-item">
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="main">
        <header className="topbar">
          <form onSubmit={search} role="search">
            <input
              className="input topbar-search"
              aria-label="Search"
              placeholder="Search requests, stories, releases…"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </form>
          <div className="topbar-user">
            <Link
              to="/notifications"
              className="bell"
              aria-label={unread ? `Notifications (${unread} unread)` : 'Notifications'}
            >
              Bell
              {unread > 0 && (
                <span className="bell-count" aria-hidden="true">
                  {unread > 99 ? '99+' : unread}
                </span>
              )}
            </Link>
            <span className="avatar" aria-hidden="true" />
            <div>
              <div className="user-name">{user.name}</div>
              <div className="user-role">{user.role_label}</div>
            </div>
            <button type="button" className="link-button" onClick={() => void signOut()}>
              Sign out
            </button>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
