import { Activity, ShieldAlert, Timer, Snowflake, Zap, Loader2 } from 'lucide-react'
import { useI18n, LANGS } from '../i18n'
import { SCENARIOS, fmtDuration, fmtMDL } from '../lib'

function Kpi({ icon: Icon, label, value, color }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-line bg-panel px-4 py-2 min-w-[170px]">
      <div className="rounded-md p-2" style={{ background: color + '22', color }}>
        <Icon size={18} />
      </div>
      <div>
        <div className="text-[11px] uppercase tracking-wide text-gray-400">{label}</div>
        <div className="text-lg font-semibold leading-tight tabular-nums">{value}</div>
      </div>
    </div>
  )
}

export default function Header({ stats, onSimulate, busy }) {
  const s = stats || {}
  const { t, lang, setLang, locale } = useI18n()
  return (
    <header className="flex flex-wrap items-center gap-4 border-b border-line bg-panel/60 px-4 py-3">
      <div className="mr-2">
        <div className="flex items-center gap-2 text-lg font-bold">
          <ShieldAlert className="text-maib" size={22} />
          MuleTrace MD <span className="text-gray-500">|</span>
          <span className="text-gray-300 font-medium">MIA Network Intelligence</span>
        </div>
        <div className="text-[11px] text-gray-500">{t('subtitle')}</div>
      </div>

      <div className="ml-auto flex flex-wrap items-center gap-2">
        <div className="mr-2 flex overflow-hidden rounded-lg border border-line text-xs font-semibold">
          {Object.entries(LANGS).map(([k, l]) => (
            <button
              key={k}
              onClick={() => setLang(k)}
              className={`px-2.5 py-2 transition ${lang === k ? 'bg-micb text-white' : 'bg-panel text-gray-400 hover:text-white'}`}
            >
              {l}
            </button>
          ))}
        </div>
        {SCENARIOS.map((sc) => (
          <button
            key={sc.slug}
            disabled={busy}
            onClick={() => onSimulate(sc.slug)}
            className={`flex items-center gap-2 rounded-lg bg-gradient-to-r ${sc.cls} px-3 py-2 text-sm font-semibold text-white shadow-lg transition hover:brightness-110 disabled:opacity-50`}
          >
            {busy ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
            {t(sc.key)}
          </button>
        ))}
      </div>
      <div className="flex w-full flex-wrap justify-end gap-3">
        <Kpi icon={Activity} label={t('kpi_tx')} value={(s.transactions_total ?? 0).toLocaleString(locale)} color="#2563EB" />
        <Kpi icon={ShieldAlert} label={t('kpi_mules')} value={s.mules_detected ?? 0} color="#ef4444" />
        <Kpi icon={Timer} label={t('kpi_dwell')} value={fmtDuration(s.avg_dwell_time, t)} color="#EAB308" />
        <Kpi icon={Snowflake} label={t('kpi_frozen')} value={fmtMDL(s.frozen_amount, locale)} color="#00A859" />
      </div>

    </header>
  )
}
