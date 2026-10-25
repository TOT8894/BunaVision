import { Outlet } from 'react-router'
import { useTheme } from '../../contexts/ThemeContext'
import { Header } from './Header'
import { Footer } from './Footer'

export function AppShell() {
  const { theme } = useTheme()

  return (
    <div
      className={`min-h-screen flex flex-col font-sans transition-colors duration-300 ${
        theme === 'dark' ? 'dark bg-[#181513] text-[#F9F7F2]' : 'bg-[#FAF8F5] text-[#1C1917]'
      }`}
    >
      <Header />
      <main className="grow">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}
