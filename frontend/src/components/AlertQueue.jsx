import { Lock, Route, Siren } from 'lucide-react'
import { bankInfo, riskColor, shortHash } from '../lib'

export default function AlertQueue({ alerts, filter, setFilter, onTrace, onFreeze }) {
  return (
    <aside className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b border-line px-4 py-2 text-sm font-semibold">
        <Siren size={16} className="text-red-500" /> Очередь алертов (maib Compliance)
      </div>
      <div className="flex gap-1 p-3">
        {[['all', 'Все банки MIA'], ['maib', 'Только клиенты maib']].map(([k, l]) => (
          <button
            key={k}
            onClick={() => setFilter(k)}
            className={`flex-1 rounded-md px-2 py-1.5 text-xs font-medium transition ${
              filter === k ? 'bg-maib text-white' : 'bg-panel text-gray-400 hover:text-white'
            }`}
          >
            {l}
          </button>
        ))}
      </div>
      <div className="flex-1 space-y-2 overflow-y-auto px-3 pb-3">
        {alerts.length === 0 && <div className="pt-8 text-center text-xs text-gray-500">Алертов нет</div>}
        {alerts.map((a) => {
          const bank = bankInfo(a.bank)
          const frozen = a.status === 'FROZEN'
          const rc = riskColor(a.risk_score)
          return (
            <div
              key={a.hash}
              className={`overflow-hidden rounded-lg border bg-panel text-xs ${frozen ? 'border-red-600' : 'border-line'}`}
              style={{ borderLeft: `4px solid ${bank.color}` }}
            >
              <div className="p-2.5">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[13px]">{shortHash(a.hash)}</span>
                  <span className="rounded px-1.5 py-0.5 font-bold" style={{ background: rc + '22', color: rc }}>
                    {a.risk_score}
                  </span>
                </div>
                <div className="mt-0.5 font-semibold" style={{ color: bank.color }}>{bank.label}</div>
                <div className="mt-2 flex flex-wrap gap-1">
                  {(a.rules || []).map((r) => (
                    <span key={r} className="rounded bg-panel2 px-1.5 py-0.5 text-[10px] text-gray-300">{r}</span>
                  ))}
                </div>
                <div className="mt-2 flex gap-2">
                  <button
                    onClick={() => onTrace(a.root_tx_id || a.hash)}
                    className="flex flex-1 items-center justify-center gap-1 rounded-md bg-micb px-2 py-1.5 font-semibold hover:brightness-110"
                  >
                    <Route size={13} /> Трассировать
                  </button>
                  <button
                    disabled={frozen}
                    onClick={() => onFreeze(a.hash)}
                    className="flex flex-1 items-center justify-center gap-1 rounded-md bg-red-600 px-2 py-1.5 font-semibold hover:bg-red-500 disabled:opacity-40"
                  >
                    <Lock size={13} /> {frozen ? 'Заморожен' : 'Заморозить'}
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </aside>
  )
}
