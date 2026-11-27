import { useEffect, useMemo, useState } from 'react'
import ReactFlow, { Background, Controls, MarkerType } from 'reactflow'
import 'reactflow/dist/style.css'
import { getTrace } from '../api'
import MuleNode from './MuleNode'

const nodeTypes = { mule: MuleNode }
const X_STEP = 280
const Y_STEP = 150

const fmtMdl = (n) => `${Math.round(n).toLocaleString('ru-RU')} MDL`
// Толщина линии ~ log(сумма): 15 MDL → ~1px, 50 000 MDL → ~7px
const strokeWidth = (amount) => Math.max(1, Math.min(8, Math.log10(Math.max(amount, 10)) * 1.5 - 0.5))

/** X = generation * 280; внутри колонки узлы упорядочены по среднему Y родителей, чтобы рёбра пересекались реже. */
function layout(nodes, edges) {
  const byGen = {}
  nodes.forEach((n) => (byGen[n.generation] ||= []).push(n))
  const y = {}
  const gens = Object.keys(byGen).map(Number).sort((a, b) => a - b)
  for (const g of gens) {
    const col = byGen[g]
    const parentY = (n) => {
      const ys = edges.filter((e) => e.to === n.account_hash && y[e.from] !== undefined).map((e) => y[e.from])
      return ys.length ? ys.reduce((a, b) => a + b, 0) / ys.length : 0
    }
    col.sort((a, b) => parentY(a) - parentY(b))
    col.forEach((n, i) => (y[n.account_hash] = (i - (col.length - 1) / 2) * Y_STEP))
  }
  return y
}

export default function DispersionGraph({ rootTxId, refreshKey, onNodeSelect, mode }) {
  const [trace, setTrace] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!rootTxId) return
    let alive = true
    setError(null)
    getTrace(rootTxId)
      .then((d) => alive && setTrace(d))
      .catch(() => alive && setError('Не удалось загрузить трассировку'))
    return () => {
      alive = false
    }
  }, [rootTxId, refreshKey])

  const { nodes, edges } = useMemo(() => {
    if (!trace) return { nodes: [], edges: [] }
    const y = layout(trace.nodes, trace.edges)
    const frozen = new Set(trace.nodes.filter((n) => n.status === 'FROZEN').map((n) => n.account_hash))
    return {
      nodes: trace.nodes.map((n) => ({
        id: n.account_hash,
        type: 'mule',
        position: { x: n.generation * X_STEP, y: y[n.account_hash] },
        data: n,
      })),
      edges: trace.edges.map((e) => {
        const color = frozen.has(e.from) ? '#6B7280' : e.is_test_tx ? '#F59E0B' : '#94A3B8'
        return {
          id: e.tx_id,
          source: e.from,
          target: e.to,
          animated: !frozen.has(e.from),
          label: fmtMdl(e.amount_mdl),
          labelStyle: { fill: '#E5E7EB', fontSize: 11, fontFamily: 'ui-monospace, monospace' },
          labelBgStyle: { fill: '#0B0F19', fillOpacity: 0.9 },
          labelBgPadding: [4, 2],
          style: {
            stroke: color,
            strokeWidth: strokeWidth(e.amount_mdl),
            strokeDasharray: e.is_test_tx || frozen.has(e.from) ? '6 4' : undefined,
          },
          markerEnd: { type: MarkerType.ArrowClosed, color },
        }
      }),
    }
  }, [trace])

  if (!rootTxId) {
    return <Placeholder>{mode === 'csv'
        ? 'Загрузите CSV, чтобы построить дерево распределения'
        : 'Запустите сценарий атаки, чтобы построить дерево распределения'}</Placeholder>
  }
  if (error) return <Placeholder>{error}</Placeholder>

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      fitView
      fitViewOptions={{ padding: 0.15 }}
      minZoom={0.2}
      nodesConnectable={false}
      onNodeClick={(_, node) => onNodeSelect?.(node.data)}
      proOptions={{ hideAttribution: true }}
    >
      <Background color="#1F2937" gap={24} />
      <Controls showInteractive={false} />
    </ReactFlow>
  )
}

function Placeholder({ children }) {
  return <div className="flex h-full items-center justify-center text-sm text-soc-muted">{children}</div>
}
