export type Health = { status: 'ok' | 'degraded'; db: 'up' | 'down' }

/**
 * Consulta GET /api/health/. Aceita 200 e 503 (ambos trazem corpo válido);
 * qualquer outra resposta ou erro de rede é lançado como exceção.
 */
export async function fetchHealth(signal?: AbortSignal): Promise<Health> {
  const response = await fetch('/api/health/', {
    signal,
    headers: { Accept: 'application/json' },
  })
  if (response.status !== 200 && response.status !== 503) {
    throw new Error(`Unexpected status ${response.status}`)
  }
  return (await response.json()) as Health
}
