import { useEffect, useRef, useState } from 'react'
import { Radio } from 'lucide-react'
import { bankInfo, fmtMDL, shortHash } from '../lib'

export default function LiveFeed() {
  const [items, setItems] = useState([])
  const [online, setOnline] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    let closed = false
    let timer
    const connect = () => {
      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      const ws = new WebSocket(`${proto}://${location.host}/ws/transactions`)
      ref.current = ws
      ws.onopen = () => setOnline(true)
      ws.onmessage = (e) => {
        try {
          const tx = JSON.parse(e.data)
          setItems((p) => [{ ...tx, _k: crypto.randomUUID() }, ...p].slice(0, 15))
        } catch {}
      }
      ws.onclose = () => {
        setOnline(false)
        if (!closed) timer = setTimeout(connect, 2000)
      }
    }
    connect()
    return () => {
      closed = true
      clearTimeout(timer)
      ref.current?.close()
    }
  }, [])

  return (
    <aside className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b border-line px-4 py-2 text-sm font-semibold">
        <Radio size={16} className={online ? 'text-maib' : 'text-gray-500'} />
        Живой поток MIA (Zero-PII)
        <span className={`ml-auto h-2 w-2 rounded-full ${online ? 'animate-pulse bg-maib' : 'bg-red-500'}`} />
      </div>
      <div className="flex-1 space-y-1 overflow-y-auto p-2 font-mono text-[11px]">
        {items.length === 0 && <div className="pt-6 text-center text-gray-500">Ожидание транзакций…</div>}
        {items.map((t) => {
          const fb = bankInfo(t.from_bank), tb = bankInfo(t.to_bank)
          return (
            <div key={t._k} className="rounded border border-line bg-panel px-2 py-1.5">
              <div className="flex justify-between text-gray-500">
                <span>{t.ts ? new Date(t.ts).toLocaleTimeString('ru-RU') : ''}</span>
                <span className="font-semibold text-gray-200">{fmtMDL(t.amount)}</span>
              </div>
              <div>{shortHash(t.from_hash)} → {shortHash(t.to_hash)}</div>
              <div>
                <span style={{ color: fb.color }}>{fb.label}</span> → <span style={{ color: tb.color }}>{tb.label}</span>
              </div>
            </div>
          )
        })}
      </div>
    </aside>
  )
}
