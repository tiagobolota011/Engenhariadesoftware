/** Erro devolvido pela API: código HTTP e corpo JSON (erros por campo ou `detail`). */
export class ApiError extends Error {
  status: number
  data: Record<string, unknown>

  constructor(status: number, data: Record<string, unknown>) {
    super(typeof data.detail === 'string' ? data.detail : `Request failed (${status}).`)
    this.status = status
    this.data = data
  }

  /** Mensagens de erro por campo, como o Django REST as devolve. */
  fieldErrors(): Record<string, string> {
    const out: Record<string, string> = {}
    for (const [field, value] of Object.entries(this.data)) {
      if (Array.isArray(value)) out[field] = value.join(' ')
    }
    return out
  }
}

export const SESSION_LOST = 'featurehub:session-lost'

function csrfToken(): string | undefined {
  return document.cookie
    .split('; ')
    .find((part) => part.startsWith('csrftoken='))
    ?.split('=')[1]
}

type Options = { method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'; body?: unknown }

export async function api<T>(path: string, { method = 'GET', body }: Options = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (method !== 'GET') {
    // As escritas levam o token CSRF; se o cookie ainda não existe, pede-se primeiro.
    if (!csrfToken()) await fetch('/api/auth/csrf/', { credentials: 'same-origin' }).catch(() => undefined)
    const token = csrfToken()
    if (token) headers['X-CSRFToken'] = token
    if (body !== undefined) headers['Content-Type'] = 'application/json'
  }
  const response = await fetch(path, {
    method,
    headers,
    credentials: 'same-origin',
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (response.status === 204) return undefined as T
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    if (response.status === 403 && !path.startsWith('/api/auth/')) {
      window.dispatchEvent(new Event(SESSION_LOST))
    }
    throw new ApiError(response.status, data && typeof data === 'object' ? data : {})
  }
  return data as T
}

export function messageOf(error: unknown, fallback: string): string {
  return error instanceof ApiError && typeof error.data.detail === 'string' ? error.message : fallback
}
