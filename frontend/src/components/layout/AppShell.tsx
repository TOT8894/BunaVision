import type { PropsWithChildren } from 'react'
import { Link, NavLink } from 'react-router'

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3 py-2 text-sm font-medium no-underline transition-colors ${
    isActive ? 'bg-coffee-100 text-coffee-700' : 'text-slate-700 hover:bg-white'
  }`

export function AppShell({ children }: PropsWithChildren) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-coffee-100 bg-white">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <Link className="text-lg font-bold text-coffee-700 no-underline" to="/">BunaVision</Link>
          <nav aria-label="Main navigation" className="flex items-center gap-1">
            <NavLink className={navLinkClass} to="/upload">New assessment</NavLink>
            <NavLink className={navLinkClass} to="/assessments">History</NavLink>
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">{children}</main>
      <footer className="border-t border-coffee-100 bg-white px-4 py-5 text-center text-sm text-slate-600">
        BunaVision provides preliminary AI predictions only. It is not an official coffee grade.
      </footer>
    </div>
  )
}
