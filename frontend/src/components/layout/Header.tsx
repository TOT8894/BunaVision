import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router'
import {
  Sun,
  Moon,
  Layers,
  Menu,
  X,
  LogIn,
  LogOut,
  UserPlus,
  User,
  Upload,
} from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import { useAuth } from '../../contexts/AuthContext'

const navItems = (isLoggedIn: boolean) => [
  { label: 'Overview', path: '/' },
  { label: 'Assess Sample', path: '/assess' },
  { label: 'Assessment History', path: '/assessments' },
  { label: 'Admin Dashboard', path: '/admin' },
  { label: 'Contacts & Support', path: '/contacts' },
  ...(!isLoggedIn ? [{ label: 'How It Works', path: '/#how-it-works' }] : []),
]

export function Header() {
  const { theme, toggleTheme } = useTheme()
  const { authToken, currentUser, authLoading, handleLogout } = useAuth()
  const navigate = useNavigate()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const onLogout = () => {
    handleLogout()
    navigate('/')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const items = navItems(!!authToken)

  return (
    <header
      className={`sticky top-0 z-40 border-b backdrop-blur-md transition-colors ${
        theme === 'dark' ? 'bg-[#181513]/90 border-[#382E26]' : 'bg-[#FAF8F5]/90 border-[#E8E0D5]'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand */}
        <Link
          to="/"
          className="flex items-center space-x-2.5 select-none group shrink-0 no-underline"
        >
          <div className="w-9 h-9 rounded-xl bg-[#593D2B] group-hover:bg-[#483020] transition-colors flex items-center justify-center shadow-md">
            <Layers className="w-5 h-5 text-[#8BA470]" />
          </div>
          <div className="hidden sm:block">
            <span className="font-extrabold text-lg tracking-tight font-serif text-[#593D2B] dark:text-[#F9F7F2]">
              BunaVision
            </span>
            <span className="ml-2 text-[9px] font-bold px-1.5 py-0.5 rounded bg-[#8BA470]/20 text-[#3A5228] dark:text-[#A7BF8C] uppercase">
              RAW BEAN OPTICAL INTELLIGENCE
            </span>
          </div>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden lg:flex items-center space-x-1">
          {items.map(({ label, path }) => (
            <NavLink
              key={path}
              to={path}
              end={path === '/'}
              className={({ isActive }) =>
                `px-3 py-1.5 rounded-lg text-sm font-medium transition-colors no-underline ${
                  isActive
                    ? 'bg-[#593D2B]/10 text-[#593D2B] dark:text-[#A7BF8C] font-semibold'
                    : 'text-[#5A544C] dark:text-[#A8A193] hover:text-[#593D2B] dark:hover:text-[#A7BF8C]'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Right controls */}
        <div className="hidden lg:flex items-center space-x-2">
          <button
            onClick={toggleTheme}
            className={`p-2 rounded-lg border transition-all cursor-pointer ${
              theme === 'dark'
                ? 'bg-[#231F1C] border-[#382E26] text-[#F9F7F2] hover:bg-[#382E26]'
                : 'bg-white border-[#E8E0D5] text-[#24211D] hover:bg-stone-50'
            }`}
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-amber-400" />
            ) : (
              <Moon className="w-4 h-4 text-[#593D2B]" />
            )}
          </button>

          {authLoading ? (
            <div className="w-24 h-8 rounded-lg bg-stone-200 dark:bg-stone-800 animate-pulse" />
          ) : authToken && currentUser ? (
            <div className="flex items-center space-x-2">
              <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#8BA470]/10 border border-[#8BA470]/20">
                <User className="w-3.5 h-3.5 text-[#8BA470]" />
                <span className="text-xs font-medium text-[#593D2B] dark:text-[#A7BF8C] max-w-32 truncate">
                  {currentUser.email}
                </span>
              </div>
              <button
                onClick={onLogout}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-[#E8E0D5] dark:border-[#382E26] text-xs font-semibold text-[#5A544C] hover:text-red-600 hover:border-red-300 transition-colors cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign Out</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <Link
                to="/login"
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-[#E8E0D5] dark:border-[#382E26] text-xs font-semibold text-[#5A544C] hover:text-[#593D2B] hover:border-[#593D2B]/30 transition-colors no-underline"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Sign In</span>
              </Link>
              <Link
                to="/register"
                className="flex items-center space-x-1.5 px-3 py-2 rounded-lg bg-[#593D2B] hover:bg-[#483020] text-white text-xs font-semibold transition-all shadow-sm no-underline"
              >
                <UserPlus className="w-3.5 h-3.5" />
                <span>Create Account</span>
              </Link>
            </div>
          )}

          {/* CTA button */}
          <Link
            to="/assess"
            className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-[#593D2B] hover:bg-[#483020] text-white text-xs font-bold transition-all shadow-md no-underline"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Assess a Sample</span>
          </Link>
        </div>

        {/* Mobile controls */}
        <div className="lg:hidden flex items-center space-x-2">
          <button
            onClick={toggleTheme}
            className={`p-2 rounded-lg border cursor-pointer ${
              theme === 'dark' ? 'bg-[#231F1C] border-[#382E26]' : 'bg-white border-[#E8E0D5]'
            }`}
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-amber-400" />
            ) : (
              <Moon className="w-4 h-4 text-[#593D2B]" />
            )}
          </button>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className={`p-2 rounded-lg border cursor-pointer ${
              theme === 'dark' ? 'bg-[#231F1C] border-[#382E26]' : 'bg-white border-[#E8E0D5]'
            }`}
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile drawer */}
      {mobileMenuOpen && (
        <div
          className={`lg:hidden border-b px-4 pt-2 pb-5 space-y-1 ${
            theme === 'dark'
              ? 'bg-[#181513] border-[#382E26]'
              : 'bg-[#FAF8F5] border-[#E8E0D5]'
          }`}
        >
          {items.map(({ label, path }) => (
            <Link
              key={path}
              to={path}
              onClick={() => setMobileMenuOpen(false)}
              className="block w-full text-left px-3 py-2.5 rounded-lg font-medium text-sm hover:bg-stone-100 dark:hover:bg-stone-800 no-underline text-inherit"
            >
              {label}
            </Link>
          ))}
          <div className="pt-2 border-t border-[#E8E0D5] dark:border-[#382E26] space-y-2">
            {authToken && currentUser ? (
              <>
                <div className="px-3 py-2 text-xs text-[#5A544C]">
                  Signed in as <strong>{currentUser.email}</strong>
                </div>
                <button
                  onClick={() => {
                    onLogout()
                    setMobileMenuOpen(false)
                  }}
                  className="w-full px-3 py-2.5 rounded-lg text-sm font-semibold text-red-600 text-left cursor-pointer hover:bg-red-50 dark:hover:bg-red-900/20"
                >
                  Sign Out
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block w-full py-2.5 rounded-xl border border-[#593D2B] text-[#593D2B] font-semibold text-sm text-center no-underline"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block w-full py-2.5 rounded-xl bg-[#593D2B] text-white font-semibold text-sm text-center no-underline"
                >
                  Create Account
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  )
}
