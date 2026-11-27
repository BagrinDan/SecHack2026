import { useRef, useState } from 'react'
import { Activity, FileUp, GitBranch, Moon, Network, RefreshCw, Repeat, RotateCcw, Sun } from 'lucide-react'
import { importCsv, simulate } from '../api'
import { LANGS, useI18n } from '../i18n'
import { useTheme } from '../theme'

const SCENARIOS = [
  { id: 'layered', Icon: GitBranch },
  { id: 'business', Icon: Network },
  { id: 'cycle', Icon: Repeat },
]

const MODES = ['simulator', 'csv']

export default function Header({ mode, onModeChange, onScenario, onImported, onReset }) {
  const { t, lang, setLang } = useI18n()
  const { theme, toggle } = useTheme()
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
      setError(e.message || t('backend_unavailable'))
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
      const vars = { name: file.name, n: res.imported, a: res.alerts.length }
      setInfo(
        res.skipped
          ? t('import_skipped', { ...vars, m: res.skipped, err: res.errors[0].error, row: res.errors[0].row })
          : t('import_done', vars),
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

        <div className="mr-2 flex overflow-hidden rounded-md border border-soc-border text-xs font-semibold" role="group" aria-label="Language">
          {Object.entries(LANGS).map(([code, label]) => (
            <button
              key={code}
              onClick={() => setLang(code)}
              className={`px-2.5 py-2 transition ${
                lang === code ? 'bg-bank-MICB text-white' : 'bg-soc-bg text-soc-muted hover:text-soc-text'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <button
          onClick={toggle}
          title={t(theme === 'dark' ? 'theme_to_light' : 'theme_to_dark')}
          aria-label={t(theme === 'dark' ? 'theme_to_light' : 'theme_to_dark')}
          className="mr-2 rounded-md border border-soc-border bg-soc-bg p-2 text-soc-muted transition hover:text-soc-text"
        >
          {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>

        <div className="mr-2 flex overflow-hidden rounded-md border border-soc-border text-sm" role="group" aria-label={t('mode_label')}>
          {MODES.map((id) => (
            <button
              key={id}
              disabled={busy !== null || mode === null}
              onClick={() => switchMode(id)}
              title={t(id === 'csv' ? 'mode_csv_hint' : 'mode_sim_hint')}
              className={`px-3 py-2 transition disabled:opacity-50 ${
                mode === id ? 'bg-bank-MAIB text-white' : 'bg-soc-bg text-soc-muted hover:text-soc-text'
              }`}
            >
              {t(id === 'csv' ? 'mode_csv' : 'mode_sim')}
            </button>
          ))}
        </div>

        {mode === 'simulator' && (
          <>
            <span className="mr-1 text-xs uppercase tracking-wide text-soc-muted">{t('attack_sim')}</span>
            {SCENARIOS.map(({ id, Icon }) => (
              <button
                key={id}
                title={t(`sc_${id}_hint`)}
                disabled={busy !== null}
                onClick={() => run(id)}
                className="flex items-center gap-2 rounded-md border border-soc-border bg-soc-bg px-3 py-2 text-sm
                           transition hover:border-bank-MAIB hover:text-soc-text disabled:opacity-50"
              >
                {busy === id ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Icon className="h-4 w-4" />}
                {t(`sc_${id}`)}
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
                         transition hover:border-bank-MAIB hover:text-soc-text disabled:opacity-50"
            >
              {busy === 'csv' ? <RefreshCw className="h-4 w-4 animate-spin" /> : <FileUp className="h-4 w-4" />}
              {t('upload_csv')}
            </button>
          </>
        )}

        <button
          disabled={busy !== null || mode === null}
          onClick={reset}
          title={t('reset_hint')}
          className="ml-2 flex items-center gap-2 rounded-md border border-risk-high/50 bg-soc-bg px-3 py-2 text-sm text-risk-high
                     transition hover:bg-risk-high/10 disabled:opacity-50"
        >
          {busy === 'reset' ? <RefreshCw className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
          {t('reset')}
        </button>
      </div>
    </header>
  )
}
