import { useState } from 'react'
import { Activity, GitBranch, Network, RefreshCw, Repeat } from 'lucide-react'
import { simulate } from '../api'

const SCENARIOS = [
  { id: 'layered', label: 'Цепочка мулов', hint: 'Кража 48 000 MDL, 4 поколения', Icon: GitBranch },
  { id: 'business', label: 'Бизнес-мул', hint: '6 источников → BUSINESS-счёт', Icon: Network },
  { id: 'cycle', label: 'Тест + цикл', hint: '15 MDL, затем 35 000 MDL по кольцу', Icon: Repeat },
]

export default function Header({ onScenario }) {
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)

  async function run(id) {
    setBusy(id)
    setError(null)
    try {
      const res = await simulate(id)
      onScenario(res)
    } catch (e) {
      setError('Бэкенд недоступен')
    } finally {
      setBusy(null)
    }
  }

  return (
    <header className="flex items-center justify-between gap-6 border-b border-soc-border bg-soc-panel px-5 py-3">
      <div className="flex items-center gap-3">
        <Activity className="h-6 w-6 text-bank-MAIB" />
        <div>
          <h1 className="text-lg font-semibold leading-tight">MuleTrace MD</h1>
          <p className="text-xs text-soc-muted">MIA Network Intelligence</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {error && <span className="mr-2 text-sm text-risk-high">{error}</span>}
        <span className="mr-1 text-xs uppercase tracking-wide text-soc-muted">Симулятор атак</span>
        {SCENARIOS.map(({ id, label, hint, Icon }) => (
          <button
            key={id}
            title={hint}
            disabled={busy !== null}
            onClick={() => run(id)}
            className="flex items-center gap-2 rounded-md border border-soc-border bg-soc-bg px-3 py-2 text-sm
                       transition hover:border-bank-MAIB hover:text-white disabled:opacity-50"
          >
            {busy === id ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Icon className="h-4 w-4" />}
            {label}
          </button>
        ))}
      </div>
    </header>
  )
}
