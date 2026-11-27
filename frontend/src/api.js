// Клиент REST API и WebSocket бэкенда MuleTrace MD.
const API_HOST = import.meta.env.VITE_API_HOST || 'localhost:8000'

export const API_URL = `http://${API_HOST}`
export const WS_URL = `ws://${API_HOST}/ws/transactions`

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`${options.method || 'GET'} ${path} → ${res.status}`)
  return res.json()
}

export const simulate = (scenario) => request(`/api/simulate/${scenario}`, { method: 'POST' })
export const getTrace = (txId, maxDepth = 5) => request(`/api/trace/${txId}?max_depth=${maxDepth}`)
export const getAlerts = (bank) => request(`/api/alerts${bank ? `?bank=${bank}` : ''}`)
// Замеряем реальное время ответа на сигнал блокировки: оно показывается в тосте.
export async function freezeAccount(hash) {
  const t0 = performance.now()
  const res = await request(`/api/accounts/${hash}/freeze`, { method: 'POST' })
  return { ...res, latency_ms: Math.max(1, Math.round(performance.now() - t0)) }
}
export const resetDemo = () => request('/api/reset', { method: 'POST' })
export const getKpi = () => request('/api/kpi')
export const getMode = () => request('/api/mode')
export const setMode = (mode) => request(`/api/mode/${mode}`, { method: 'POST' })

// Загрузка CSV: тело запроса — сам файл. Сообщение об ошибке берём из поля detail ответа бэкенда.
export async function importCsv(file) {
  const res = await fetch(`${API_URL}/api/import/csv`, {
    method: 'POST',
    headers: { 'Content-Type': 'text/csv' },
    body: file,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `Ошибка загрузки (${res.status})`)
  return data
}

export function connectTransactions(onTx) {
  const ws = new WebSocket(WS_URL)
  ws.onmessage = (e) => onTx(JSON.parse(e.data))
  return ws
}
