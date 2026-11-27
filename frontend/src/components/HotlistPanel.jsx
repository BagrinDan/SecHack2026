import { useEffect, useState } from 'react'
import { Lock, Target } from 'lucide-react'
import { getKpi } from '../api'
import { BANK_COLORS, BANK_LABELS } from '../constants'
import { fmtMdl, useI18n } from '../i18n'

const POLL_MS = 2500

export default function HotlistPanel({ refreshKey }) {
  const { t, locale } = useI18n()
  const [kpi, setKpi] = useState(null)

  useEffect(() => {
    let alive = true
    const load = () =>
      getKpi()
        .then((d) => alive && setKpi(d))
        .catch(() => {})
    load()
    const id = setInterval(load, POLL_MS)
    return () => {
      alive = false
      clearInterval(id)
    }
  }, [refreshKey])

  const hotlist = kpi?.endpoint_hotlist ?? []
  const byBank = kpi?.mules_by_bank ?? {}
  const total = Object.values(byBank).reduce((a, b) => a + b, 0)
  const maxCount = Math.max(1, ...Object.values(byBank))

  return (
    <aside className="flex h-full flex-col overflow-y-auto rounded-lg border border-soc-border bg-soc-panel">
      <section className="border-b border-soc-border p-3 pb-2">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <Target className="h-4 w-4 text-risk-high" /> {t('hot_title')}
        </h2>
        <p className="mt-0.5 text-xs text-soc-muted">{t('hot_sub')}</p>
        <ul className="mt-2 space-y-1.5">
          {hotlist.length === 0 && <li className="py-4 text-center text-xs text-soc-muted">{t('no_data')}</li>}
          {hotlist.map((r, i) => (
            <li key={r.account_hash} className="rounded-md border border-soc-border bg-soc-bg px-2.5 py-1.5 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold" style={{ color: BANK_COLORS[r.bank_code] }}>
                  {i + 1}. {BANK_LABELS[r.bank_code]}
                </span>
                <span className="flex items-center gap-1 font-mono font-semibold">
                  {r.status === 'FROZEN' && <Lock className="h-3 w-3 text-risk-high" />}
                  {fmtMdl(r.total_in_mdl, locale)}
                </span>
              </div>
              <div className="mt-0.5 flex justify-between font-mono text-soc-muted">
                <span>{r.account_hash}</span>
                <span>{t('trees_n', { n: r.tree_count })}</span>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="p-3">
        <h2 className="text-sm font-semibold">{t('mules_by_bank')}</h2>
        <p className="mt-0.5 text-xs text-soc-muted">{t('total_detected', { n: total })}</p>
        <ul className="mt-2 space-y-1.5">
          {Object.keys(BANK_LABELS).map((code) => {
            const n = byBank[code] ?? 0
            return (
              <li key={code} className="text-xs">
                <div className="flex justify-between">
                  <span style={{ color: BANK_COLORS[code] }}>{BANK_LABELS[code]}</span>
                  <span className="font-mono">{n}</span>
                </div>
                <div className="mt-0.5 h-1 overflow-hidden rounded bg-soc-bg">
                  <div
                    className="h-full rounded transition-all"
                    style={{ width: `${(n / maxCount) * 100}%`, background: BANK_COLORS[code] }}
                  />
                </div>
              </li>
            )
          })}
        </ul>
      </section>
    </aside>
  )
}
