import { useEffect, useState } from 'react'
import { Clock, Lock, ShieldAlert, Wallet } from 'lucide-react'
import { getKpi } from '../api'

const POLL_MS = 2500

const fmtInt = (n) => (n ?? 0).toLocaleString('ru-RU')
const fmtDwell = (s) => {
  if (s == null) return '—'
  return s >= 60 ? `${(s / 60).toFixed(1)} мин` : `${Math.round(s)} с`
}

export default function KpiBar({ refreshKey }) {
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
    { label: 'Проверено транзакций', value: fmtInt(kpi?.transactions_checked), Icon: ShieldAlert, tone: 'text-bank-MICB' },
    { label: 'Выявлено счетов-мулов', value: fmtInt(kpi?.mules_detected), Icon: ShieldAlert, tone: 'text-risk-high' },
    { label: 'Средний Dwell Time', value: fmtDwell(kpi?.avg_dwell_time_sec), Icon: Clock, tone: 'text-risk-mid' },
    { label: 'Заблокировано, MDL', value: fmtInt(kpi?.blocked_amount_mdl), Icon: Lock, tone: 'text-risk-low' },
  ]

  return (
    <section className="grid grid-cols-4 gap-4 px-5 py-4">
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
