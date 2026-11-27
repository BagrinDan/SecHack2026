import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

export const LANGS = { ro: 'RO', ru: 'RU', en: 'ENG' }
const LOCALES = { ro: 'ro-RO', ru: 'ru-RU', en: 'en-US' }

const dict = {
  ru: {
    subtitle: 'Мониторинг в реальном времени · Zero-PII',
    kpi_tx: 'Транзакций в MIA',
    kpi_mules: 'Выявлено мулов',
    kpi_dwell: 'Средний Dwell Time',
    kpi_frozen: 'Заморожено (MDL)',
    atk_gen4_drops: 'Атака: Дропы 4-го поколения',
    atk_business_mule: 'Атака: Бизнес-мул',
    atk_test_ring: 'Атака: Тест + Кольцо',
    graph_title: 'Дерево распределения (Dispersion Tree)',
    root: 'Корень',
    graph_empty: 'Запустите симулятор атак или нажмите «Трассировать» в очереди алертов',
    victim: 'Жертва',
    generation: 'Поколение',
    status: 'Статус',
    active: 'ACTIVE',
    frozen: 'FROZEN',
    test: 'тест',
    freeze_full: 'Заблокировать счёт (maib / MIA Alert)',
    queue_title: 'Очередь алертов (maib Compliance)',
    f_all: 'Все банки MIA',
    f_maib: 'Только клиенты maib',
    no_alerts: 'Алертов нет',
    trace: 'Трассировать',
    freeze: 'Заморозить',
    frozen_done: 'Заморожен',
    live_title: 'Живой поток MIA (Zero-PII)',
    waiting: 'Ожидание транзакций…',
    backend_down: 'Бэкенд недоступен',
    u_s: 'с', u_min: 'мин', u_h: 'ч',
  },
  ro: {
    subtitle: 'Monitorizare în timp real · Zero-PII',
    kpi_tx: 'Tranzacții în MIA',
    kpi_mules: 'Mule detectate',
    kpi_dwell: 'Dwell Time mediu',
    kpi_frozen: 'Înghețat (MDL)',
    atk_gen4_drops: 'Atac: Drop-uri generația 4',
    atk_business_mule: 'Atac: Mule de business',
    atk_test_ring: 'Atac: Test + Inel',
    graph_title: 'Arborele de dispersie (Dispersion Tree)',
    root: 'Rădăcină',
    graph_empty: 'Rulați simulatorul de atacuri sau apăsați „Urmărește” în coada de alerte',
    victim: 'Victimă',
    generation: 'Generația',
    status: 'Stare',
    active: 'ACTIVE',
    frozen: 'FROZEN',
    test: 'test',
    freeze_full: 'Blochează contul (maib / MIA Alert)',
    queue_title: 'Coada de alerte (maib Compliance)',
    f_all: 'Toate băncile MIA',
    f_maib: 'Doar clienți maib',
    no_alerts: 'Nu există alerte',
    trace: 'Urmărește',
    freeze: 'Îngheață',
    frozen_done: 'Înghețat',
    live_title: 'Flux live MIA (Zero-PII)',
    waiting: 'Se așteaptă tranzacții…',
    backend_down: 'Backend indisponibil',
    u_s: 's', u_min: 'min', u_h: 'h',
  },
  en: {
    subtitle: 'Real-time monitoring · Zero-PII',
    kpi_tx: 'Transactions in MIA',
    kpi_mules: 'Mules detected',
    kpi_dwell: 'Average Dwell Time',
    kpi_frozen: 'Frozen (MDL)',
    atk_gen4_drops: 'Attack: 4th-gen drops',
    atk_business_mule: 'Attack: Business mule',
    atk_test_ring: 'Attack: Test + Ring',
    graph_title: 'Dispersion Tree',
    root: 'Root',
    graph_empty: 'Run the attack simulator or click “Trace” in the alert queue',
    victim: 'Victim',
    generation: 'Generation',
    status: 'Status',
    active: 'ACTIVE',
    frozen: 'FROZEN',
    test: 'test',
    freeze_full: 'Block account (maib / MIA Alert)',
    queue_title: 'Alert queue (maib Compliance)',
    f_all: 'All MIA banks',
    f_maib: 'maib customers only',
    no_alerts: 'No alerts',
    trace: 'Trace',
    freeze: 'Freeze',
    frozen_done: 'Frozen',
    live_title: 'MIA live stream (Zero-PII)',
    waiting: 'Waiting for transactions…',
    backend_down: 'Backend unavailable',
    u_s: 's', u_min: 'min', u_h: 'h',
  },
}

const Ctx = createContext(null)

export function I18nProvider({ children }) {
  const [lang, setLang] = useState(() => {
    const s = localStorage.getItem('lang')
    return s in dict ? s : 'ru'
  })
  useEffect(() => {
    localStorage.setItem('lang', lang)
    document.documentElement.lang = lang
  }, [lang])
  const t = useCallback((k) => dict[lang][k] ?? k, [lang])
  const value = useMemo(() => ({ lang, setLang, t, locale: LOCALES[lang] }), [lang, t])
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export const useI18n = () => useContext(Ctx)
