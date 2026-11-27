import { Handle, Position } from 'reactflow'
import { Lock } from 'lucide-react'
import { BANK_COLORS, BANK_LABELS } from '../constants'

const riskColor = (r) => (r >= 60 ? '#EF4444' : r >= 30 ? '#F59E0B' : '#22C55E')

function fmtDwell(s) {
  if (s == null) return '—'
  return s >= 60 ? `${(s / 60).toFixed(1)} мин` : `${Math.round(s)} с`
}

export default function MuleNode({ data, selected }) {
  const frozen = data.status === 'FROZEN'
  const color = BANK_COLORS[data.bank_code] || '#6B7280'
  const genLabel = data.generation === 0 ? 'Жертва / источник' : `Поколение ${data.generation}`

  return (
    <div
      className={`w-[220px] overflow-hidden rounded-lg bg-soc-panel text-xs shadow-lg ${
        selected ? 'ring-2 ring-white/60' : ''
      }`}
      style={{ border: `2px solid ${frozen ? '#EF4444' : '#1F2937'}` }}
    >
      <Handle type="target" position={Position.Left} className="!bg-soc-muted" />
      <div className="h-1.5" style={{ background: color }} />
      <div className="space-y-1.5 p-2.5">
        <div className="flex items-center justify-between">
          <span className="font-semibold" style={{ color }}>
            {BANK_LABELS[data.bank_code] || data.bank_code}
          </span>
          <span className="flex items-center gap-1">
            {frozen && <Lock className="h-3.5 w-3.5 text-risk-high" />}
            <span
              className="rounded px-1.5 py-0.5 font-mono font-semibold text-black"
              style={{ background: riskColor(data.risk_score) }}
              title="Risk Score"
            >
              {data.risk_score}
            </span>
          </span>
        </div>
        <div className="font-mono text-soc-text">
          {data.account_hash.slice(0, 6)}…{data.account_hash.slice(-4)}
          {data.account_type === 'BUSINESS' && <span className="ml-1 text-soc-muted">[BIZ]</span>}
        </div>
        <div className="flex justify-between text-soc-muted">
          <span>{genLabel}</span>
          <span>Dwell: {fmtDwell(data.dwell_time_sec)}</span>
        </div>
        {frozen && <div className="font-semibold text-risk-high">FROZEN</div>}
      </div>
      <Handle type="source" position={Position.Right} className="!bg-soc-muted" />
    </div>
  )
}
