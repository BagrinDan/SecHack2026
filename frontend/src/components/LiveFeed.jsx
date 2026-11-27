import { useEffect, useRef, useState } from 'react'
import { Radio } from 'lucide-react'
import { useI18n } from '../i18n'
import { bankInfo, fmtMDL, shortHash } from '../lib'

export default function LiveFeed() {
  const { t, locale } = useI18n()
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
        {t('live_title')}
        <span className={`ml-auto h-2 w-2 rounded-full ${online ? 'animate-pulse bg-maib' : 'bg-red-500'}`} />
      </div>
      <div className="flex-1 space-y-1 overflow-y-auto p-2 font-mono text-[11px]">
        {items.length === 0 && <div className="pt-6 text-center text-gray-500">{t('waiting')}</div>}
        {items.map((tx) => {
          const fb = bankInfo(tx.from_bank), tb = bankInfo(tx.to_bank)
          return (
            <div key={tx._k} className="rounded border border-line bg-panel px-2 py-1.5">
              <div className="flex justify-between text-gray-500">
                <span>{tx.ts ? new Date(tx.ts).toLocaleTimeString(locale) : ''}</span>
                <span className="font-semibold text-gray-200">{fmtMDL(tx.amount, locale)}</span>
              </div>
              <div>{shortHash(tx.from_hash)} → {shortHash(tx.to_hash)}</div>
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
