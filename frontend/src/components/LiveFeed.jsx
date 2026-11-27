import { useEffect, useState } from 'react'
import { connectTransactions } from '../api'
import { BANK_COLORS, BANK_LABELS } from '../constants'

const MAX_ROWS = 40

export default function LiveFeed() {
  const [rows, setRows] = useState([])
  const [online, setOnline] = useState(false)

  useEffect(() => {
    let ws
    let timer
    let closed = false
    const open = () => {
      ws = connectTransactions((tx) => setRows((r) => [tx, ...r].slice(0, MAX_ROWS)))
      ws.onopen = () => setOnline(true)
      ws.onclose = () => {
        setOnline(false)
        if (!closed) timer = setTimeout(open, 2000)
      }
    }
    open()
    return () => {
      closed = true
      clearTimeout(timer)
      ws?.close()
    }
  }, [])

  return (
    <section className="mx-5 mb-5 h-44 shrink-0 overflow-hidden rounded-lg border border-soc-border bg-soc-panel">
      <div className="flex items-center justify-between border-b border-soc-border px-3 py-1.5 text-xs">
        <span className="font-semibold">Живая лента MIA</span>
        <span className={online ? 'text-risk-low' : 'text-risk-high'}>● {online ? 'online' : 'reconnecting…'}</span>
      </div>
      <ul className="h-[calc(100%-29px)] overflow-y-auto font-mono text-xs">
        {rows.map((t) => (
          <li key={t.tx_id} className="flex items-center gap-3 px-3 py-0.5 odd:bg-soc-bg/40">
            <span className="text-soc-muted">{new Date(t.timestamp).toLocaleTimeString('ru-RU')}</span>
            <span className="w-24 truncate" style={{ color: BANK_COLORS[t.from_bank] }}>{BANK_LABELS[t.from_bank]}</span>
            <span>{t.from_hash.slice(0, 6)}</span>
            <span className="text-soc-muted">→</span>
            <span className="w-24 truncate" style={{ color: BANK_COLORS[t.to_bank] }}>{BANK_LABELS[t.to_bank]}</span>
            <span>{t.to_hash.slice(0, 6)}</span>
            <span className={`ml-auto ${t.amount_mdl >= 10000 ? 'font-semibold text-risk-mid' : ''}`}>
              {t.amount_mdl.toLocaleString('ru-RU')} MDL
            </span>
            <span className="w-14 text-right text-soc-muted">{t.channel.replace('MIA_', '')}</span>
          </li>
        ))}
        {rows.length === 0 && <li className="p-3 text-soc-muted">Ожидание транзакций…</li>}
      </ul>
    </section>
  )
}
