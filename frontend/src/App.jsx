import { useEffect, useState } from 'react'
import Header from './components/Header'
import KpiBar from './components/KpiBar'
import DispersionGraph from './components/DispersionGraph'
import AlertQueue from './components/AlertQueue'
import LiveFeed from './components/LiveFeed'
import NodeDetailsDrawer from './components/NodeDetailsDrawer'
import HotlistPanel from './components/HotlistPanel'
import Toast from './components/Toast'
import { getAutoPrevent, getMode, resetDemo, setAutoPrevent, setMode } from './api'
import { BANK_LABELS } from './constants'
import { fmtMdl, useI18n } from './i18n'

export default function App() {
  const { t, locale } = useI18n()
  // root_tx_id выбранной трассировки — по нему граф запрашивает дерево
  const [rootTxId, setRootTxId] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0) // форсирует обновление KPI, алертов и графа
  const [selected, setSelected] = useState(null)

  const [mode, setModeState] = useState(null) // 'simulator' | 'csv'; null, пока режим не получен от бэкенда
  const [feedKey, setFeedKey] = useState(0) // пересоздаёт живую ленту при смене режима

  const [tab, setTab] = useState('alerts') // правая панель: 'alerts' | 'hotlist'
  const [toast, setToast] = useState(null)
  const [autoPrevent, setAutoPreventState] = useState(null) // автоблокировка: true / false, null — ещё не загружено

  const refresh = () => setRefreshKey((n) => n + 1)

  useEffect(() => {
    getMode().then((r) => setModeState(r.mode)).catch(() => setModeState('simulator'))
    getAutoPrevent().then((r) => setAutoPreventState(r.enabled)).catch(() => setAutoPreventState(null))
  }, [])

  // Бэкенд сбрасывает данные при переключении, поэтому очищаем и выбранное дерево, и ленту.
  async function handleModeChange(next) {
    const r = await setMode(next)
    setModeState(r.mode)
    setRootTxId(null)
    setSelected(null)
    setFeedKey((n) => n + 1)
    refresh()
  }

  // Чистый перезапуск перед показом: бэкенд очищает данные, интерфейс — выбранное дерево и ленту.
  async function handleReset() {
    await resetDemo()
    setRootTxId(null)
    setSelected(null)
    setToast(null)
    setFeedKey((n) => n + 1)
    refresh()
  }

  async function handleAutoPreventChange(enabled) {
    const r = await setAutoPrevent(enabled)
    setAutoPreventState(r.enabled)
  }

  // Сообщаем, сколько автоблокировка остановила: это главный результат прогона.
  function notifyPrevented(res) {
    if (res.blocked_tx_count > 0) {
      setToast(t('toast_prevented', { n: res.blocked_tx_count, amount: fmtMdl(res.rejected_amount_mdl, locale) }))
    }
  }

  function handleImported(res) {
    notifyPrevented(res)
    setRootTxId(res.root_tx_id)
    setSelected(null)
    refresh()
  }

  function handleScenario(res) {
    notifyPrevented(res)
    setRootTxId(res.root_tx_id)
    setSelected(null)
    refresh()
  }

  function handleFrozen(res) {
    if (!res.already_frozen) {
      setToast(t('toast_block', { bank: BANK_LABELS[res.bank_code], ms: res.latency_ms, amount: fmtMdl(res.prevented_mdl, locale) }))
    }
    setSelected((s) => (s && s.account_hash === res.account_hash ? { ...s, status: 'FROZEN' } : s))
    refresh()
  }

  return (
    <div className="flex h-full flex-col bg-soc-bg text-soc-text">
      <Header mode={mode} onModeChange={handleModeChange} onScenario={handleScenario} onImported={handleImported} onReset={handleReset} autoPrevent={autoPrevent} onAutoPreventChange={handleAutoPreventChange} />
      <KpiBar refreshKey={refreshKey} />
      <div className="mx-5 mb-4 flex min-h-0 flex-1 gap-4">
        <main className="relative min-w-0 flex-1 overflow-hidden rounded-lg border border-soc-border bg-soc-panel">
          <DispersionGraph rootTxId={rootTxId} refreshKey={refreshKey} onNodeSelect={setSelected} mode={mode} />
          <NodeDetailsDrawer
            key={selected?.account_hash}
            node={selected}
            onClose={() => setSelected(null)}
            onFrozen={handleFrozen}
          />
        </main>
        <div className="flex h-full w-[340px] shrink-0 flex-col gap-2">
          <div className="flex rounded-md border border-soc-border bg-soc-panel p-0.5 text-xs" role="tablist">
            {[
              ['alerts', t('tab_alerts')],
              ['hotlist', t('tab_hotlist')],
            ].map(([id, label]) => (
              <button
                key={id}
                role="tab"
                aria-selected={tab === id}
                onClick={() => setTab(id)}
                className={`flex-1 rounded px-2 py-1.5 transition ${
                  tab === id ? 'bg-soc-border text-soc-text' : 'text-soc-muted hover:text-soc-text'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          {/* обе панели смонтированы, чтобы не терять фильтр и не перезапрашивать данные при переключении */}
          <div className={`min-h-0 flex-1 ${tab === 'alerts' ? '' : 'hidden'}`}>
            <AlertQueue
              refreshKey={refreshKey}
              onTrace={(id) => {
                setRootTxId(id)
                setSelected(null)
              }}
              onChanged={handleFrozen}
            />
          </div>
          <div className={`min-h-0 flex-1 ${tab === 'hotlist' ? '' : 'hidden'}`}>
            <HotlistPanel refreshKey={refreshKey} />
          </div>
        </div>
      </div>
      <LiveFeed key={feedKey} />
      <Toast toast={toast} onClose={() => setToast(null)} />
    </div>
  )
}
