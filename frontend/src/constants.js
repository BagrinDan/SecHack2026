// Цвета банков MIA (тёмная тема синхронизирована с tailwind.config.js)
// Значения берутся из CSS-переменных (index.css): в светлой теме оттенки темнее, чтобы текст читался на белом.
// Использовать только в style={{...}}, не в SVG-атрибутах.
export const BANK_COLORS = {
  MAIB: 'var(--bank-MAIB)',
  MICB: 'var(--bank-MICB)',
  VICTORIABANK: 'var(--bank-VICTORIABANK)',
  OTP: 'var(--bank-OTP)',
  FINCOMBANK: 'var(--bank-FINCOMBANK)',
}

export const BANK_LABELS = {
  MAIB: 'maib',
  MICB: 'MICB',
  VICTORIABANK: 'Victoriabank',
  OTP: 'OTP Bank',
  FINCOMBANK: 'FinComBank',
}
