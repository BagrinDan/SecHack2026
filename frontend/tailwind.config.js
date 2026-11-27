/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Цвета интерфейса задаются CSS-переменными (см. index.css), поэтому работают в обеих темах
        soc: {
          bg: 'rgb(var(--soc-bg) / <alpha-value>)',
          panel: 'rgb(var(--soc-panel) / <alpha-value>)',
          border: 'rgb(var(--soc-border) / <alpha-value>)',
          text: 'rgb(var(--soc-text) / <alpha-value>)',
          muted: 'rgb(var(--soc-muted) / <alpha-value>)',
        },
        // Цвета банков Молдовы
        bank: {
          MAIB: '#E31E24',
          MICB: '#1E88E5',
          VICTORIABANK: '#2E7D32',
          OTP: '#7CB342',
          FINCOMBANK: '#F9A825',
        },
        risk: { low: '#22C55E', mid: '#F59E0B', high: '#EF4444' },
      },
      fontFamily: { mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'] },
    },
  },
  plugins: [],
}
