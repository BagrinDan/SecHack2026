import { useCallback, useEffect, useState } from 'react'
import { AlertTriangle } from 'lucide-react'
import Header from './components/Header'
import TraceGraph from './components/TraceGraph'
import AlertQueue from './components/AlertQueue'
import LiveFeed from './components/LiveFeed'
import { api } from './lib'
import { useI18n } from './i18n'

export default function App() {
  const { t } = useI18n()
  const [stats, setStats] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [filter, setFilter] = useState('all')
  const [rootTx, setRootTx] = useState(null)
  const [trace, setTrace] = useState(null)
  const [selected, setSelected] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const guard = useCallback(async (fn) => {
    try { setError(null); return await fn() } catch (e) { setError(e.message) }
  }, [])

  const refresh = useCallback(async () => {
    try {
      const [s, a] = await Promise.all([api.stats(), api.alerts(filter === 'maib' ? 'maib' : null)])
      setStats(s); setAlerts(a); setError(null)
    } catch (e) { setError(t('backend_down') + ': ' + e.message) }
  }, [filter, t])

  const loadTrace = useCallback(async (tx) => {
    const t = await api.trace(tx)
    setTrace({ root_tx_id: tx, ...t })
  }, [])

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 3000)
    return () => clearInterval(id)
  }, [refresh])

  const trace_ = (tx) => guard(async () => { setRootTx(tx); setSelected(null); await loadTrace(tx) })

  const simulate = (slug) => guard(async () => {
    setBusy(true)
    try {
      const { root_tx_id } = await api.simulate(slug)
      await trace_(root_tx_id)
      refresh()
    } finally { setBusy(false) }
  })

  const freeze = (hash) => guard(async () => {
    await api.freeze(hash)
    if (rootTx) await loadTrace(rootTx)
    refresh()
  })

  return (
    <div className="flex h-full flex-col bg-bg">
      <Header stats={stats} onSimulate={simulate} busy={busy} />
      {error && (
        <div className="flex items-center gap-2 bg-red-950 px-4 py-1.5 text-xs text-red-300">
          <AlertTriangle size={14} /> {error}
        </div>
      )}
      <main className="flex min-h-0 flex-1">
        <div className="w-[60%] border-r border-line">
          <TraceGraph trace={trace} selected={selected} onSelect={setSelected} onFreeze={freeze} />
        </div>
        <div className="w-[25%] border-r border-line">
          <AlertQueue alerts={alerts} filter={filter} setFilter={setFilter} onTrace={trace_} onFreeze={freeze} />
        </div>
        <div className="w-[15%] min-w-[190px]">
          <LiveFeed />
        </div>
      </main>
    </div>
  )
}
