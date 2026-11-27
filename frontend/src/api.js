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
export const freezeAccount = (hash) => request(`/api/accounts/${hash}/freeze`, { method: 'POST' })
export const getKpi = () => request('/api/kpi')

export function connectTransactions(onTx) {
  const ws = new WebSocket(WS_URL)
  ws.onmessage = (e) => onTx(JSON.parse(e.data))
  return ws
}
