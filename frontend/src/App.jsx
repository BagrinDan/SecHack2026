import { useState } from 'react'
import Header from './components/Header'
import KpiBar from './components/KpiBar'

export default function App() {
  // root_tx_id последнего сценария — по нему граф (коммит 10) запрашивает трассировку
  const [rootTxId, setRootTxId] = useState(null)
  const [scenarioRuns, setScenarioRuns] = useState(0)

  function handleScenario(res) {
    setRootTxId(res.root_tx_id)
    setScenarioRuns((n) => n + 1) // форсирует мгновенное обновление KPI
  }

  return (
    <div className="flex h-full flex-col bg-soc-bg text-soc-text">
      <Header onScenario={handleScenario} />
      <KpiBar refreshKey={scenarioRuns} />
      <main className="mx-5 mb-5 flex flex-1 items-center justify-center rounded-lg border border-dashed border-soc-border text-sm text-soc-muted">
        {rootTxId ? (
          <span>
            Корневая транзакция: <code className="font-mono text-soc-text">{rootTxId}</code>
          </span>
        ) : (
          'Запустите сценарий атаки, чтобы построить дерево распределения'
        )}
      </main>
    </div>
  )
}
