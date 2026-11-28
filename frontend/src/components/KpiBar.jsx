import { useEffect, useState } from 'react'
import { Clock, Lock, ShieldAlert, ShieldOff, Wallet } from 'lucide-react'
import { getKpi } from '../api'
import { fmtDwell, useI18n } from '../i18n'

const POLL_MS = 2500

export default function KpiBar({ refreshKey }) {
  const { t, locale } = useI18n()
  const fmtInt = (n) => (n ?? 0).toLocaleString(locale)
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

  const cards = [
    { label: t('kpi_tx'), value: fmtInt(kpi?.transactions_checked), Icon: ShieldAlert, tone: 'text-bank-MICB' },
    { label: t('kpi_mules'), value: fmtInt(kpi?.mules_detected), Icon: ShieldAlert, tone: 'text-risk-high' },
    { label: t('kpi_dwell'), value: fmtDwell(kpi?.avg_dwell_time_sec, t), Icon: Clock, tone: 'text-risk-mid' },
    { label: t('kpi_blocked'), value: fmtInt(kpi?.blocked_amount_mdl), Icon: Lock, tone: 'text-risk-low' },
    { label: t('kpi_rejected'), value: kpi?.rejected_amount_mdl == null ? '—' : fmtInt(kpi.rejected_amount_mdl), Icon: ShieldOff, tone: 'text-risk-low' },
  ]

  return (
    <section className="grid grid-cols-5 gap-4 px-5 py-4">
      {cards.map(({ label, value, Icon, tone }) => (
        <div key={label} className="rounded-lg border border-soc-border bg-soc-panel p-4">
          <div className="flex items-center justify-between text-xs uppercase tracking-wide text-soc-muted">
            {label}
            <Icon className={`h-4 w-4 ${tone}`} />
          </div>
          <div className="mt-2 font-mono text-2xl font-semibold tabular-nums">{value}</div>
        </div>
      ))}
    </section>
  )
}
