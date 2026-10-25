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
  Shield,
  Upload,
} from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import { useAuth } from '../../contexts/AuthContext'

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

  const handleAssessClick = (e: React.MouseEvent) => {
    if (!authToken) {
      e.preventDefault()
      navigate('/login', { state: { from: '/assess' } })
    }
  }

  const isAdmin = currentUser?.role === 'admin'

  return (
    <header
      className={`sticky top-0 z-40 border-b backdrop-blur-md transition-colors ${
        theme === 'dark'
          ? 'bg-[#181513]/95 border-[#382E26]'
          : 'bg-[#FAF8F5]/95 border-[#E2D9CF]'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand */}
        <Link
          to="/"
          className="flex items-center space-x-3 select-none group shrink-0 no-underline"
        >
          <div className="w-9 h-9 rounded-xl bg-[#593D2B] group-hover:bg-[#483020] transition-colors flex items-center justify-center shadow-xs">
            <Layers className="w-5 h-5 text-[#8BA470]" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="font-extrabold text-xl tracking-tight font-serif text-[#382416] dark:text-[#F9F7F2]">
              BunaVision
            </span>
            <span className="hidden sm:inline-block text-xs font-bold px-2 py-0.5 rounded-full bg-[#8BA470]/20 text-[#3A5228] dark:text-[#A7BF8C] tracking-wide uppercase">
              Optical Intelligence
            </span>
          </div>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center space-x-1">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `px-3.5 py-2 rounded-xl text-sm font-semibold transition-colors no-underline ${
                isActive
                  ? 'bg-[#593D2B]/10 text-[#382416] dark:text-[#F9F7F2]'
                  : 'text-[#44403C] dark:text-[#D6D3D1] hover:text-[#1C1917] dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5'
              }`
            }
          >
            Overview
          </NavLink>

          <NavLink
            to="/assess"
            onClick={handleAssessClick}
            className={({ isActive }) =>
              `px-3.5 py-2 rounded-xl text-sm font-semibold transition-colors no-underline flex items-center gap-1.5 ${
                isActive
                  ? 'bg-[#593D2B]/10 text-[#382416] dark:text-[#F9F7F2]'
                  : 'text-[#44403C] dark:text-[#D6D3D1] hover:text-[#1C1917] dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5'
              }`
            }
          >
            <Upload className="w-4 h-4 text-[#593D2B] dark:text-[#8BA470]" />
            <span>Assess Sample</span>
          </NavLink>

          {/* Assessment History: Signed-in users only */}
          {authToken && (
            <NavLink
              to="/assessments"
              className={({ isActive }) =>
                `px-3.5 py-2 rounded-xl text-sm font-semibold transition-colors no-underline ${
                  isActive
                    ? 'bg-[#593D2B]/10 text-[#382416] dark:text-[#F9F7F2]'
                    : 'text-[#44403C] dark:text-[#D6D3D1] hover:text-[#1C1917] dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5'
                }`
              }
            >
              Assessment History
            </NavLink>
          )}

          {/* Admin Dashboard: Admin only */}
          {isAdmin && (
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                `px-3.5 py-2 rounded-xl text-sm font-semibold transition-colors no-underline flex items-center gap-1.5 ${
                  isActive
                    ? 'bg-[#593D2B]/10 text-[#382416] dark:text-[#F9F7F2]'
                    : 'text-[#44403C] dark:text-[#D6D3D1] hover:text-[#1C1917] dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5'
                }`
              }
            >
              <Shield className="w-3.5 h-3.5 text-[#8BA470]" />
              <span>Admin Dashboard</span>
            </NavLink>
          )}
        </nav>

        {/* Right controls */}
        <div className="hidden md:flex items-center space-x-2.5">
          {/* Theme Toggle */}
          <button
            type="button"
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className={`p-2 rounded-xl border transition-all cursor-pointer ${
              theme === 'dark'
                ? 'bg-[#231F1C] border-[#382E26] text-[#F9F7F2] hover:bg-[#382E26]'
                : 'bg-white border-[#E2D9CF] text-[#24211D] hover:bg-stone-100'
            }`}
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-amber-400" />
            ) : (
              <Moon className="w-4 h-4 text-[#593D2B]" />
            )}
          </button>

          {authLoading ? (
            <div className="w-24 h-9 rounded-xl bg-stone-200 dark:bg-stone-800 animate-pulse" />
          ) : authToken && currentUser ? (
            <div className="flex items-center space-x-2">
              <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl border bg-white dark:bg-[#231F1C] border-[#E2D9CF] dark:border-[#382E26] shadow-xs">
                <span className="text-xs font-semibold text-[#1C1917] dark:text-[#F9F7F2] max-w-40 truncate">
                  {currentUser.email}
                </span>
                {isAdmin && (
                  <span className="text-xs font-bold px-1.5 py-0.5 rounded bg-[#8BA470]/20 text-[#3A5228] dark:text-[#A7BF8C] uppercase">
                    Admin
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={onLogout}
                className="flex items-center space-x-1.5 px-3 py-2 rounded-xl border border-[#E2D9CF] dark:border-[#382E26] text-xs font-semibold text-[#44403C] dark:text-[#D6D3D1] hover:text-red-700 hover:border-red-300 dark:hover:text-red-400 transition-colors cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign Out</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <Link
                to="/login"
                className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl border border-[#E2D9CF] dark:border-[#382E26] text-xs font-bold text-[#382416] dark:text-[#F9F7F2] hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors no-underline"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Sign In</span>
              </Link>
              <Link
                to="/register"
                className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-[#593D2B] hover:bg-[#483020] text-white text-xs font-bold transition-all shadow-xs no-underline"
              >
                <UserPlus className="w-3.5 h-3.5" />
                <span>Create Account</span>
              </Link>
            </div>
          )}
        </div>

        {/* Mobile menu button */}
        <div className="md:hidden flex items-center space-x-2">
          <button
            type="button"
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className={`p-2 rounded-xl border cursor-pointer ${
              theme === 'dark' ? 'bg-[#231F1C] border-[#382E26]' : 'bg-white border-[#E2D9CF]'
            }`}
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-amber-400" />
            ) : (
              <Moon className="w-4 h-4 text-[#593D2B]" />
            )}
          </button>
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className={`p-2 rounded-xl border cursor-pointer ${
              theme === 'dark' ? 'bg-[#231F1C] border-[#382E26]' : 'bg-white border-[#E2D9CF]'
            }`}
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile drawer */}
      {mobileMenuOpen && (
        <div
          className={`md:hidden border-b px-4 pt-2 pb-5 space-y-2 ${
            theme === 'dark'
              ? 'bg-[#181513] border-[#382E26]'
              : 'bg-[#FAF8F5] border-[#E2D9CF]'
          }`}
        >
          <Link
            to="/"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-xl text-sm font-semibold text-[#1C1917] dark:text-[#F9F7F2] no-underline hover:bg-black/5"
          >
            Overview
          </Link>

          <Link
            to="/assess"
            onClick={(e) => {
              setMobileMenuOpen(false)
              handleAssessClick(e)
            }}
            className="block px-3 py-2 rounded-xl text-sm font-semibold text-[#1C1917] dark:text-[#F9F7F2] no-underline hover:bg-black/5"
          >
            Assess Sample
          </Link>

          {authToken && (
            <Link
              to="/assessments"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 rounded-xl text-sm font-semibold text-[#1C1917] dark:text-[#F9F7F2] no-underline hover:bg-black/5"
            >
              Assessment History
            </Link>
          )}

          {isAdmin && (
            <Link
              to="/admin"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 rounded-xl text-sm font-semibold text-[#1C1917] dark:text-[#F9F7F2] no-underline hover:bg-black/5"
            >
              Admin Dashboard
            </Link>
          )}

          <div className="pt-3 border-t border-[#E2D9CF] dark:border-[#382E26]">
            {authToken && currentUser ? (
              <div className="space-y-2">
                <div className="text-xs text-[#44403C] dark:text-[#D6D3D1] px-3">
                  Signed in as <strong className="text-[#1C1917] dark:text-white">{currentUser.email}</strong>
                  {isAdmin && <span className="ml-1 text-[#4F7335] font-bold">(Admin)</span>}
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setMobileMenuOpen(false)
                    onLogout()
                  }}
                  className="w-full text-left px-3 py-2 rounded-xl text-xs font-semibold text-red-700 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/20"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <div className="flex flex-col gap-2 pt-1">
                <Link
                  to="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-4 py-2 text-center rounded-xl border border-[#E2D9CF] dark:border-[#382E26] text-xs font-bold text-[#382416] dark:text-[#F9F7F2] no-underline"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-4 py-2 text-center rounded-xl bg-[#593D2B] text-white text-xs font-bold no-underline"
                >
                  Create Account
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  )
}
