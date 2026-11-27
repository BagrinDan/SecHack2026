/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        soc: { bg: '#0B0F19', panel: '#121826', border: '#1F2937', text: '#E5E7EB', muted: '#9CA3AF' },
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
