import { useEffect } from 'react'
import { ShieldCheck, X } from 'lucide-react'
import { useI18n } from '../i18n'

export default function Toast({ toast, onClose }) {
  const { t } = useI18n()
  useEffect(() => {
    if (!toast) return
    const id = setTimeout(onClose, 6000)
    return () => clearTimeout(id)
  }, [toast, onClose])

  if (!toast) return null
  return (
    <div
      role="status"
      className="fixed bottom-6 left-1/2 z-50 flex max-w-xl -translate-x-1/2 items-start gap-3 rounded-lg border border-risk-low/60
                 bg-soc-panel px-4 py-3 text-sm shadow-2xl"
    >
      <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-risk-low" />
      <span>{toast}</span>
      <button onClick={onClose} aria-label={t('close')} className="text-soc-muted hover:text-soc-text">
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}
