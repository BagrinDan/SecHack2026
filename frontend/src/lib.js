export const BANKS = {
  MAIB: { label: 'MAIB', color: '#00A859' },
  MICB: { label: 'MICB', color: '#2563EB' },
  VICTORIABANK: { label: 'VICTORIABANK', color: '#EAB308' },
  OTP: { label: 'OTP', color: '#84CC16' },
  FINCOMBANK: { label: 'FINCOMBANK', color: '#A855F7' },
}

export const bankInfo = (b) => BANKS[String(b || '').toUpperCase()] || { label: b || '—', color: '#6b7280' }

export const shortHash = (h) => (h && h.length > 12 ? `${h.slice(0, 6)}…${h.slice(-4)}` : h || '')

export const fmtMDL = (n, locale = 'ru-RU') => `${Math.round(n || 0).toLocaleString(locale)} MDL`

export function fmtDuration(sec, t = (k) => ({ u_s: 'с', u_min: 'мин', u_h: 'ч' })[k]) {
  if (sec == null) return '—'
  if (sec < 60) return `${Math.round(sec)} ${t('u_s')}`
  if (sec < 3600) return `${Math.round(sec / 60)} ${t('u_min')}`
  return `${(sec / 3600).toFixed(1)} ${t('u_h')}`
}

export const riskColor = (r) => (r >= 80 ? '#ef4444' : r >= 50 ? '#f59e0b' : '#22c55e')

export const SCENARIOS = [
  { slug: 'gen4_drops', key: 'atk_gen4_drops', cls: 'from-red-600 to-rose-500' },
  { slug: 'business_mule', key: 'atk_business_mule', cls: 'from-amber-600 to-orange-500' },
  { slug: 'test_ring', key: 'atk_test_ring', cls: 'from-fuchsia-600 to-purple-500' },
]

async function req(url, opts) {
  const r = await fetch(url, opts)
  if (!r.ok) throw new Error(`${r.status} ${url}`)
  return r.json()
}

export const api = {
  stats: () => req('/api/stats'),
  alerts: (bank) => req(`/api/alerts${bank ? `?bank=${bank}` : ''}`),
  trace: (txId) => req(`/api/trace/${encodeURIComponent(txId)}`),
  simulate: (s) => req(`/api/simulate/${s}`, { method: 'POST' }),
  freeze: (hash) => req(`/api/accounts/${encodeURIComponent(hash)}/freeze`, { method: 'POST' }),
}
