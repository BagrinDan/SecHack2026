import { useEffect, useState } from 'react'
import { Lock, Radar } from 'lucide-react'
import { freezeAccount, getAlerts } from '../api'
import { BANK_COLORS, BANK_LABELS } from '../constants'
import { useI18n } from '../i18n'

const POLL_MS = 2500
const RULE_LABELS = {
  RAPID_HOP: 'Rapid Hop',
  FAN_OUT: 'Fan-Out',
  CYCLING: 'Cycling',
  TEST_TRANSACTION: 'Test Tx',
  MULTI_TREE: 'Multi-tree',
}

export default function AlertQueue({ refreshKey, onTrace, onChanged }) {
  const { t } = useI18n()
  const [alerts, setAlerts] = useState([])
  const [onlyMaib, setOnlyMaib] = useState(false)
  const [busy, setBusy] = useState(null)

  useEffect(() => {
    let alive = true
    const load = () =>
      getAlerts(onlyMaib ? 'MAIB' : undefined)
        .then((d) => alive && setAlerts(d))
        .catch(() => {})
    load()
    const id = setInterval(load, POLL_MS)
    return () => {
      alive = false
      clearInterval(id)
    }
  }, [onlyMaib, refreshKey])

  async function freeze(a) {
    setBusy(a.account_hash)
    try {
      const res = await freezeAccount(a.account_hash)
      onChanged?.(res)
    } finally {
      setBusy(null)
    }
  }

  return (
    <aside className="flex h-full w-[340px] shrink-0 flex-col rounded-lg border border-soc-border bg-soc-panel">
      <div className="border-b border-soc-border p-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold">{t('alert_queue')}</h2>
          <span className="rounded bg-risk-high/20 px-2 py-0.5 font-mono text-xs text-risk-high">{alerts.length}</span>
        </div>
        <div className="mt-2 flex rounded-md bg-soc-bg p-0.5 text-xs">
          {[
            [false, t('f_all')],
            [true, t('f_maib')],
          ].map(([val, label]) => (
            <button
              key={label}
              onClick={() => setOnlyMaib(val)}
              className={`flex-1 rounded px-2 py-1.5 transition ${
                onlyMaib === val ? 'bg-soc-border text-soc-text' : 'text-soc-muted hover:text-soc-text'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <ul className="flex-1 space-y-2 overflow-y-auto p-3">
        {alerts.length === 0 && <li className="py-8 text-center text-xs text-soc-muted">{t('no_alerts')}</li>}
        {alerts.map((a) => {
          const frozen = a.status === 'FROZEN'
          return (
            <li key={a.alert_id} className="rounded-md border border-soc-border bg-soc-bg p-2.5 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold" style={{ color: BANK_COLORS[a.bank_code] }}>
                  {BANK_LABELS[a.bank_code]}
                </span>
                <span className="rounded bg-risk-high px-1.5 py-0.5 font-mono font-semibold text-black">{a.risk_score}</span>
              </div>
              <div className="mt-1 font-mono text-soc-text">{a.account_hash}</div>
              <div className="mt-1.5 flex flex-wrap gap-1">
                {a.rules.map((r) => (
                  <span key={r} className="rounded bg-soc-border px-1.5 py-0.5 text-soc-muted">
                    {RULE_LABELS[r] || r}
                  </span>
                ))}
              </div>
              <div className="mt-1.5 text-soc-muted">
                {a.generation != null && <>{t('generation')} {a.generation} · </>}{t('trees')}: {a.tree_count}
              </div>
              <div className="mt-2 flex gap-2">
                <button
                  disabled={!a.root_tx_id}
                  onClick={() => onTrace(a.root_tx_id)}
                  className="flex flex-1 items-center justify-center gap-1.5 rounded border border-soc-border py-1.5 hover:border-bank-MICB disabled:opacity-40"
                >
                  <Radar className="h-3.5 w-3.5" /> {t('trace')}
                </button>
                <button
                  disabled={frozen || busy === a.account_hash}
                  onClick={() => freeze(a)}
                  className="flex flex-1 items-center justify-center gap-1.5 rounded border border-risk-high/60 py-1.5 text-risk-high hover:bg-risk-high/10 disabled:opacity-40"
                >
                  <Lock className="h-3.5 w-3.5" /> {frozen ? t('frozen') : t('freeze')}
                </button>
              </div>
            </li>
          )
        })}
      </ul>
    </aside>
  )
}
