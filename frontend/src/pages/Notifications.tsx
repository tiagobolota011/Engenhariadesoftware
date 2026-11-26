import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listNotifications, markAllRead, markRead, notificationsChanged } from '../api/notifications'
import type { AppNotification } from '../api/types'
import Badge from '../components/Badge'
import { formatDate, plural } from '../format'

/** Notifications: menções, mudanças de estado e decisões nos pedidos (UC-09). */
export default function Notifications() {
  const navigate = useNavigate()
  const [unreadOnly, setUnreadOnly] = useState(false)
  const [items, setItems] = useState<AppNotification[] | null>(null)
  const [unread, setUnread] = useState(0)
  const [failed, setFailed] = useState(false)
  const [actionError, setActionError] = useState('')

  const load = useCallback(() => {
    setFailed(false)
    listNotifications(unreadOnly)
      .then((data) => {
        setItems(data.results)
        setUnread(data.unread)
      })
      .catch(() => setFailed(true))
  }, [unreadOnly])

  useEffect(load, [load])

  async function open(item: AppNotification) {
    setActionError('')
    if (!item.read) {
      try {
        await markRead(item.id)
        notificationsChanged()
      } catch {
        // Abrir o pedido é o que importa; fica por ler e pode tentar-se de novo.
      }
    }
    navigate(`/requests/${item.request_id}`)
  }

  async function readAll() {
    setActionError('')
    try {
      await markAllRead()
      notificationsChanged()
      load()
    } catch {
      setActionError('The notifications could not be marked as read. Try again.')
    }
  }

  return (
    <>
      <h1 className="page-title">Notifications</h1>
      <div className="toolbar">
        <label className="checkbox">
          <input type="checkbox" checked={unreadOnly} onChange={(event) => setUnreadOnly(event.target.checked)} />
          Unread only
        </label>
        <span className="muted">{plural(unread, 'unread notification')}</span>
        <button type="button" className="btn" disabled={unread === 0} onClick={() => void readAll()}>
          Mark all as read
        </button>
      </div>
      {actionError && (
        <p className="banner banner-error" role="alert">
          {actionError}
        </p>
      )}
      {failed && (
        <p className="banner banner-error" role="alert">
          Your notifications could not be loaded. Reload the page to try again.
        </p>
      )}
      {!failed && items === null && <p className="muted">Loading notifications…</p>}
      {items !== null &&
        (items.length === 0 ? (
          <p className="empty">
            {unreadOnly
              ? 'You are all caught up.'
              : 'No notifications yet. You will be told here when someone mentions you or one of your requests changes.'}
          </p>
        ) : (
          <ul className="notification-list">
            {items.map((item) => (
              <li key={item.id} className={item.read ? 'notification' : 'notification notification-unread'}>
                <button type="button" className="notification-open" onClick={() => void open(item)}>
                  <span className="notification-message">{item.message}</span>
                  <span className="request-meta">
                    {item.actor_name} · {formatDate(item.created_at)}
                  </span>
                </button>
                <Badge variant={item.read ? 'outline' : 'filled'}>{item.read ? item.kind_label : `New · ${item.kind_label}`}</Badge>
              </li>
            ))}
          </ul>
        ))}
    </>
  )
}
