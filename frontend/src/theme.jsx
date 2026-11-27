import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

const Ctx = createContext(null)

// Тема хранится в атрибуте data-theme на <html>; сам атрибут до первой отрисовки ставит скрипт в index.html.
export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => (localStorage.getItem('theme') === 'light' ? 'light' : 'dark'))

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggle = useCallback(() => setTheme((t) => (t === 'dark' ? 'light' : 'dark')), [])
  const value = useMemo(() => ({ theme, toggle }), [theme, toggle])
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export const useTheme = () => useContext(Ctx)

// Цвет точек фона графа: SVG-атрибут не умеет CSS-переменные, поэтому задаём значением.
export const GRAPH_GRID = { dark: '#1F2937', light: '#D1D5DB' }
