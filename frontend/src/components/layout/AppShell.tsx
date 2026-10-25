import type { PropsWithChildren } from 'react'
import { Link, NavLink } from 'react-router'
import { Layers, History, ShieldAlert } from 'lucide-react'
import { env } from '../../config/env'
import { Disclaimer } from '../common/Disclaimer'
import bunavision from '../../assets/bunavision-favicon.ico'

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
    isActive
      ? 'bg-coffee-100 text-coffee-700 shadow-2xs font-semibold'
      : 'text-slate-600 hover:bg-coffee-50 hover:text-coffee-700'
  }`

export function AppShell({ children }: PropsWithChildren) {
  return (
    <div className="flex min-h-screen flex-col bg-coffee-50 font-sans text-slate-900 antialiased">
      {/* Dev mock banner if enabled */}
      {env.useMocks && (
        <div className="bg-amber-500 text-amber-950 px-4 py-1 text-center text-xs font-semibold tracking-wide">
          DEVELOPMENT MOCK MODE ACTIVE — Responses are simulated and not real model inferences
        </div>
      )}

      {/* Header */}
      <header className="sticky top-0 z-30 border-b border-coffee-100 bg-white/95 backdrop-blur-xs">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <Link
            to="/"
            className="flex items-center gap-2 text-lg font-bold text-coffee-700 no-underline transition-opacity hover:opacity-90"
            aria-label="BunaVision home"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-coffee-700 text-white shadow-xs">
              <img src={bunavision} alt="buna vision logo" className="h-10 w-10" aria-hidden="true" />
            </span>
            <span className="tracking-tight">BunaVision</span>
          </Link>

          <nav aria-label="Main navigation" className="flex items-center gap-2">
            <NavLink className={navLinkClass} to="/assess">
              <Layers className="h-4 w-4" aria-hidden="true" />
              <span>Assess Sample</span>
            </NavLink>
            <NavLink className={navLinkClass} to="/assessments">
              <History className="h-4 w-4" aria-hidden="true" />
              <span>History</span>
            </NavLink>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6 sm:py-8">{children}</main>

      {/* Footer with mandatory disclaimer */}
      <footer className="border-t border-coffee-100 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
          <div className="mb-4">
            <Disclaimer variant="compact" />
          </div>
          <div className="flex flex-col items-center justify-between gap-3 text-xs text-slate-500 sm:flex-row">
            <p>
              © {new Date().getFullYear()} BunaVision — Preliminary AI green coffee defect
              screening.
            </p>
            <div className="flex items-center gap-2 text-slate-400">
              <ShieldAlert className="h-3.5 w-3.5 text-slate-400" aria-hidden="true" />
              <span>Decision-support only. Not an official grade.</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
