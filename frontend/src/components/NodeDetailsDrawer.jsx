import { useState } from 'react'
import { Lock, X } from 'lucide-react'
import { freezeAccount } from '../api'
import { BANK_COLORS, BANK_LABELS } from '../constants'
import { fmtDwell, fmtMdl, useI18n } from '../i18n'

export default function NodeDetailsDrawer({ node, onClose, onFrozen }) {
  const { t, locale } = useI18n()
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
      setError(true)
    } finally {
      setBusy(false)
    }
  }

  const rows = [
    [t('d_bank'), BANK_LABELS[node.bank_code]],
    [t('d_type'), node.account_type],
    [t('d_status'), node.status],
    [t('generation'), node.generation],
    [t('d_received'), fmtMdl(node.total_in, locale)],
    [t('d_sent'), fmtMdl(node.total_out, locale)],
    [t('d_outgoing'), node.fan_out],
    ['Dwell Time', fmtDwell(node.dwell_time_sec, t)],
  ]

  return (
    <div className="absolute right-3 top-3 z-10 w-72 rounded-lg border border-soc-border bg-soc-panel/95 p-3 text-xs shadow-xl backdrop-blur">
      <div className="flex items-start justify-between">
        <div>
          <div className="font-semibold" style={{ color: BANK_COLORS[node.bank_code] }}>{t('details')}</div>
          <div className="mt-0.5 font-mono text-soc-text">{node.account_hash}</div>
        </div>
        <button onClick={onClose} aria-label={t('close')} className="text-soc-muted hover:text-soc-text">
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

      {error && <div className="mt-2 text-risk-high">{t('freeze_error')}</div>}

      {confirm ? (
        <div className="mt-3 rounded border border-risk-high/60 p-2">
          <div>{t('confirm_text', { bank: BANK_LABELS[node.bank_code] })}</div>
          <div className="mt-2 flex gap-2">
            <button disabled={busy} onClick={doFreeze} className="flex-1 rounded bg-risk-high py-1.5 font-semibold text-black disabled:opacity-50">
              {t('confirm')}
            </button>
            <button onClick={() => setConfirm(false)} className="flex-1 rounded border border-soc-border py-1.5">{t('cancel')}</button>
          </div>
        </div>
      ) : (
        <button
          disabled={frozen}
          onClick={() => setConfirm(true)}
          className="mt-3 flex w-full items-center justify-center gap-2 rounded border border-risk-high/60 py-2 text-risk-high hover:bg-risk-high/10 disabled:opacity-40"
        >
          <Lock className="h-4 w-4" /> {frozen ? t('account_frozen') : t('block')}
        </button>
      )}
    </div>
  )
}
