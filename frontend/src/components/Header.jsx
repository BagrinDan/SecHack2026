import { useRef, useState } from 'react'
import { Activity, FileUp, GitBranch, Network, RefreshCw, Repeat, RotateCcw } from 'lucide-react'
import { importCsv, simulate } from '../api'

const SCENARIOS = [
  { id: 'layered', label: 'Цепочка мулов', hint: 'Кража 48 000 MDL, 4 поколения', Icon: GitBranch },
  { id: 'business', label: 'Бизнес-мул', hint: '6 источников → BUSINESS-счёт', Icon: Network },
  { id: 'cycle', label: 'Тест + цикл', hint: '15 MDL, затем 35 000 MDL по кольцу', Icon: Repeat },
]

const MODES = [
  { id: 'simulator', label: 'Симулятор' },
  { id: 'csv', label: 'CSV' },
]

export default function Header({ mode, onModeChange, onScenario, onImported, onReset }) {
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)
  const [info, setInfo] = useState(null)
  const fileRef = useRef(null)

  async function guarded(id, fn) {
    setBusy(id)
    setError(null)
    try {
      await fn()
    } catch (e) {
      setError(e.message || 'Бэкенд недоступен')
    } finally {
      setBusy(null)
    }
  }

  const run = (id) => guarded(id, async () => onScenario(await simulate(id)))

  const switchMode = (id) =>
    id !== mode &&
    guarded('mode', async () => {
      setInfo(null)
      await onModeChange(id)
    })

  const reset = () => guarded('reset', async () => { setInfo(null); await onReset() })

  const upload = (file) =>
    file &&
    guarded('csv', async () => {
      const res = await importCsv(file)
      setInfo(
        `${file.name}: загружено ${res.imported}` +
          (res.skipped ? `, пропущено ${res.skipped} (${res.errors[0].error}, строка ${res.errors[0].row})` : '') +
          `, алертов ${res.alerts.length}`,
      )
      onImported(res)
    })

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
        {error && <span className="mr-2 max-w-md truncate text-sm text-risk-high" title={error}>{error}</span>}
        {!error && info && mode === 'csv' && (
          <span className="mr-2 max-w-md truncate text-sm text-soc-muted" title={info}>{info}</span>
        )}

        <div className="mr-2 flex overflow-hidden rounded-md border border-soc-border text-sm" role="group" aria-label="Режим данных">
          {MODES.map(({ id, label }) => (
            <button
              key={id}
              disabled={busy !== null || mode === null}
              onClick={() => switchMode(id)}
              title={id === 'csv' ? 'Данные из загруженного файла' : 'Встроенный поток и сценарии атак'}
              className={`px-3 py-2 transition disabled:opacity-50 ${
                mode === id ? 'bg-bank-MAIB text-white' : 'bg-soc-bg text-soc-muted hover:text-white'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {mode === 'simulator' && (
          <>
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
          </>
        )}

        {mode === 'csv' && (
          <>
            <input
              ref={fileRef}
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={(e) => {
                upload(e.target.files[0])
                e.target.value = '' // позволяет загрузить тот же файл повторно
              }}
            />
            <button
              disabled={busy !== null}
              onClick={() => fileRef.current?.click()}
              className="flex items-center gap-2 rounded-md border border-soc-border bg-soc-bg px-3 py-2 text-sm
                         transition hover:border-bank-MAIB hover:text-white disabled:opacity-50"
            >
              {busy === 'csv' ? <RefreshCw className="h-4 w-4 animate-spin" /> : <FileUp className="h-4 w-4" />}
              Загрузить CSV
            </button>
          </>
        )}

        <button
          disabled={busy !== null || mode === null}
          onClick={reset}
          title="Очистить граф, алерты и KPI для чистого показа"
          className="ml-2 flex items-center gap-2 rounded-md border border-risk-high/50 bg-soc-bg px-3 py-2 text-sm text-risk-high
                     transition hover:bg-risk-high/10 disabled:opacity-50"
        >
          {busy === 'reset' ? <RefreshCw className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
          Сбросить демо
        </button>
      </div>
    </header>
  )
}
