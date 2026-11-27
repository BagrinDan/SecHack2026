import { useMemo } from 'react'
import ReactFlow, { Background, Controls, MarkerType } from 'reactflow'
import { Lock, X, Network } from 'lucide-react'
import MuleNode from './MuleNode'
import { bankInfo, fmtDuration, fmtMDL, riskColor } from '../lib'

const nodeTypes = { mule: MuleNode }
const COL_W = 300
const ROW_H = 130

function layout(trace) {
  const byGen = {}
  trace.nodes.forEach((n) => (byGen[n.generation ?? 0] ||= []).push(n))
  const maxRows = Math.max(1, ...Object.values(byGen).map((a) => a.length))
  const nodes = []
  Object.entries(byGen).forEach(([g, arr]) => {
    const offset = ((maxRows - arr.length) * ROW_H) / 2
    arr.forEach((n, i) =>
      nodes.push({
        id: n.hash,
        type: 'mule',
        position: { x: Number(g) * COL_W, y: offset + i * ROW_H },
        data: n,
      }),
    )
  })
  const amounts = trace.edges.map((e) => e.amount || 0)
  const max = Math.max(1, ...amounts)
  const edges = trace.edges.map((e, i) => {
    const color = e.is_test ? '#f59e0b' : '#60a5fa'
    return {
      id: e.id || `e${i}`,
      source: e.source,
      target: e.target,
      animated: true,
      label: `${fmtMDL(e.amount)}${e.is_test ? ' · тест' : ''}`,
      labelStyle: { fill: '#e5e7eb', fontSize: 11, fontWeight: 600 },
      labelBgStyle: { fill: '#0B0F19' },
      labelBgPadding: [4, 2],
      style: {
        stroke: color,
        strokeWidth: 1.5 + ((e.amount || 0) / max) * 6,
        strokeDasharray: e.is_test ? '6 5' : undefined,
      },
      markerEnd: { type: MarkerType.ArrowClosed, color },
    }
  })
  return { nodes, edges }
}

export default function TraceGraph({ trace, selected, onSelect, onFreeze, freezing }) {
  const { nodes, edges } = useMemo(() => (trace ? layout(trace) : { nodes: [], edges: [] }), [trace])
  const sel = selected && trace?.nodes.find((n) => n.hash === selected)
  const bank = sel && bankInfo(sel.bank)

  return (
    <section className="relative flex h-full flex-col">
      <div className="flex items-center gap-2 border-b border-line px-4 py-2 text-sm font-semibold">
        <Network size={16} className="text-micb" /> Дерево распределения (Dispersion Tree)
        {trace && <span className="ml-2 text-xs font-normal text-gray-500">Корень: {trace.root_tx_id}</span>}
      </div>
      <div className="relative flex-1">
        {!trace && (
          <div className="absolute inset-0 z-10 flex items-center justify-center text-sm text-gray-500">
            Запустите симулятор атак или нажмите «Трассировать» в очереди алертов
          </div>
        )}
        <ReactFlow
          nodes={nodes.map((n) => ({ ...n, selected: n.id === selected }))}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodeClick={(_, n) => onSelect(n.id)}
          onPaneClick={() => onSelect(null)}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          minZoom={0.2}
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#1f2a3d" gap={24} />
          <Controls showInteractive={false} />
        </ReactFlow>

        {sel && (
          <div className="absolute right-3 top-3 z-20 w-64 rounded-lg border border-line bg-panel p-3 text-xs shadow-2xl">
            <div className="flex items-center justify-between">
              <span className="font-bold" style={{ color: bank.color }}>{bank.label}</span>
              <button onClick={() => onSelect(null)} className="text-gray-400 hover:text-white"><X size={14} /></button>
            </div>
            <div className="mt-1 break-all font-mono text-[11px] text-gray-300">{sel.hash}</div>
            <dl className="mt-2 space-y-1">
              <Row k="Поколение" v={sel.generation === 0 ? 'Жертва' : `Gen ${sel.generation}`} />
              <Row k="Risk Score" v={<b style={{ color: riskColor(sel.risk_score) }}>{sel.risk_score ?? 0}</b>} />
              <Row k="Dwell Time" v={fmtDuration(sel.dwell_time)} />
              <Row k="Статус" v={sel.status === 'FROZEN' ? <span className="text-red-500">FROZEN</span> : sel.status || 'ACTIVE'} />
            </dl>
            <button
              disabled={sel.status === 'FROZEN' || freezing}
              onClick={() => onFreeze(sel.hash)}
              className="mt-3 flex w-full items-center justify-center gap-2 rounded-md bg-red-600 px-3 py-2 font-semibold text-white hover:bg-red-500 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Lock size={14} /> Заблокировать счёт (maib / MIA Alert)
            </button>
          </div>
        )}
      </div>
    </section>
  )
}

const Row = ({ k, v }) => (
  <div className="flex justify-between"><dt className="text-gray-400">{k}</dt><dd>{v}</dd></div>
)
