import { useState } from 'react'
import { Lock, X } from 'lucide-react'
import { freezeAccount } from '../api'
import { BANK_COLORS, BANK_LABELS } from '../constants'

const mdl = (n) => `${Math.round(n ?? 0).toLocaleString('ru-RU')} MDL`

export default function NodeDetailsDrawer({ node, onClose, onFrozen }) {
  const [confirm, setConfirm] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  if (!node) return null
  const frozen = node.status === 'FROZEN'

  async function doFreeze() {
    setBusy(true)
    setError(null)
    try {
      const res = await freezeAccount(node.account_hash)
      setConfirm(false)
      onFrozen(res)
    } catch {
      setError('Не удалось отправить сигнал блокировки')
    } finally {
      setBusy(false)
    }
  }

  const rows = [
    ['Банк', BANK_LABELS[node.bank_code]],
    ['Тип счёта', node.account_type],
    ['Статус', node.status],
    ['Поколение', node.generation],
    ['Получено', mdl(node.total_in)],
    ['Отправлено', mdl(node.total_out)],
    ['Исходящих переводов', node.fan_out],
    ['Dwell Time', node.dwell_time_sec == null ? '—' : `${Math.round(node.dwell_time_sec)} с`],
  ]

  return (
    <div className="absolute right-3 top-3 z-10 w-72 rounded-lg border border-soc-border bg-soc-panel/95 p-3 text-xs shadow-xl backdrop-blur">
      <div className="flex items-start justify-between">
        <div>
          <div className="font-semibold" style={{ color: BANK_COLORS[node.bank_code] }}>Детали счёта</div>
          <div className="mt-0.5 font-mono text-soc-text">{node.account_hash}</div>
        </div>
        <button onClick={onClose} aria-label="Закрыть" className="text-soc-muted hover:text-white">
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="mt-3 flex items-center gap-2">
        <span className="text-soc-muted">Risk Score</span>
        <span className="rounded bg-risk-high px-1.5 py-0.5 font-mono font-semibold text-black">{node.risk_score}</span>
      </div>
      <div className="mt-1.5 flex flex-wrap gap-1">
        {node.rules?.map((r) => (
          <span key={r} className="rounded bg-soc-border px-1.5 py-0.5 text-soc-muted">{r}</span>
        ))}
      </div>

      <dl className="mt-3 space-y-1">
        {rows.map(([k, v]) => (
          <div key={k} className="flex justify-between">
            <dt className="text-soc-muted">{k}</dt>
            <dd className="font-mono">{v}</dd>
          </div>
        ))}
      </dl>

      {error && <div className="mt-2 text-risk-high">{error}</div>}

      {confirm ? (
        <div className="mt-3 rounded border border-risk-high/60 p-2">
          <div>Заморозить счёт в {BANK_LABELS[node.bank_code]}? Сигнал блокировки уйдёт в банк-владелец.</div>
          <div className="mt-2 flex gap-2">
            <button disabled={busy} onClick={doFreeze} className="flex-1 rounded bg-risk-high py-1.5 font-semibold text-black disabled:opacity-50">
              Подтвердить
            </button>
            <button onClick={() => setConfirm(false)} className="flex-1 rounded border border-soc-border py-1.5">Отмена</button>
          </div>
        </div>
      ) : (
        <button
          disabled={frozen}
          onClick={() => setConfirm(true)}
          className="mt-3 flex w-full items-center justify-center gap-2 rounded border border-risk-high/60 py-2 text-risk-high hover:bg-risk-high/10 disabled:opacity-40"
        >
          <Lock className="h-4 w-4" /> {frozen ? 'Счёт заморожен' : 'Заблокировать счёт'}
        </button>
      )}
    </div>
  )
}
