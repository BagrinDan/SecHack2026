import { Handle, Position } from 'reactflow'
import { Lock, User } from 'lucide-react'
import { bankInfo, fmtDuration, riskColor, shortHash } from '../lib'

export default function MuleNode({ data, selected }) {
  const bank = bankInfo(data.bank)
  const frozen = data.status === 'FROZEN'
  const isVictim = data.generation === 0
  const rc = riskColor(data.risk_score ?? 0)
  return (
    <div
      className={`relative w-[200px] overflow-hidden rounded-lg bg-panel2 text-xs shadow-xl ${
        frozen ? 'border-2 border-red-500 shadow-red-900/50' : selected ? 'border-2 border-white' : 'border border-line'
      }`}
    >
      <Handle type="target" position={Position.Left} className="!bg-gray-500" />
      <div className="flex">
        <div className="w-1.5" style={{ background: bank.color }} />
        <div className="flex-1 p-2">
          <div className="flex items-center justify-between">
            <span className="font-semibold" style={{ color: bank.color }}>{bank.label}</span>
            {frozen ? <Lock size={14} className="text-red-500" /> : isVictim && <User size={14} className="text-gray-400" />}
          </div>
          <div className="mt-0.5 font-mono text-[13px]">{shortHash(data.hash)}</div>
          <div className="mt-2 flex items-center justify-between">
            <span className="text-gray-400">{isVictim ? 'Жертва' : `Gen ${data.generation}`}</span>
            {!isVictim && (
              <span className="rounded px-1.5 py-0.5 font-bold" style={{ background: rc + '22', color: rc }}>
                Risk {data.risk_score ?? 0}
              </span>
            )}
          </div>
          {!isVictim && <div className="mt-1 text-gray-400">Dwell: {fmtDuration(data.dwell_time)}</div>}
          {frozen && <div className="mt-1 font-bold text-red-500">FROZEN</div>}
        </div>
      </div>
      <Handle type="source" position={Position.Right} className="!bg-gray-500" />
    </div>
  )
}
