import { useState } from 'react'
import Header from './components/Header'
import KpiBar from './components/KpiBar'
import DispersionGraph from './components/DispersionGraph'
import AlertQueue from './components/AlertQueue'
import LiveFeed from './components/LiveFeed'
import NodeDetailsDrawer from './components/NodeDetailsDrawer'

export default function App() {
  // root_tx_id выбранной трассировки — по нему граф запрашивает дерево
  const [rootTxId, setRootTxId] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0) // форсирует обновление KPI, алертов и графа
  const [selected, setSelected] = useState(null)

  const refresh = () => setRefreshKey((n) => n + 1)

  function handleScenario(res) {
    setRootTxId(res.root_tx_id)
    setSelected(null)
    refresh()
  }

  function handleFrozen(res) {
    setSelected((s) => (s && s.account_hash === res.account_hash ? { ...s, status: 'FROZEN' } : s))
    refresh()
  }

  return (
    <div className="flex h-full flex-col bg-soc-bg text-soc-text">
      <Header onScenario={handleScenario} />
      <KpiBar refreshKey={refreshKey} />
      <div className="mx-5 mb-4 flex min-h-0 flex-1 gap-4">
        <main className="relative min-w-0 flex-1 overflow-hidden rounded-lg border border-soc-border bg-soc-panel">
          <DispersionGraph rootTxId={rootTxId} refreshKey={refreshKey} onNodeSelect={setSelected} />
          <NodeDetailsDrawer
            key={selected?.account_hash}
            node={selected}
            onClose={() => setSelected(null)}
            onFrozen={handleFrozen}
          />
        </main>
        <AlertQueue
          refreshKey={refreshKey}
          onTrace={(id) => {
            setRootTxId(id)
            setSelected(null)
          }}
          onChanged={handleFrozen}
        />
      </div>
      <LiveFeed />
    </div>
  )
}
