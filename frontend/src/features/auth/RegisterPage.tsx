import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router'
import { ArrowLeft, Mail, Lock, RefreshCw, UserPlus, AlertTriangle } from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import { useAuth } from '../../contexts/AuthContext'

export function RegisterPage() {
  const { theme } = useTheme()
  const { handleRegister, registerError, registerLoading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [localError, setLocalError] = useState<string | null>(null)

  const card = `rounded-2xl border transition-all ${
    theme === 'dark'
      ? 'bg-[#231F1C] border-[#382E26] shadow-sm'
      : 'bg-white border-[#E2D9CF] shadow-xs'
  }`
  const inputCls = `w-full px-3.5 py-2.5 rounded-xl text-sm border focus:outline-none focus:ring-2 focus:ring-[#8BA470] transition-colors ${
    theme === 'dark'
      ? 'bg-[#181513] border-[#382E26] text-[#F9F7F2]'
      : 'bg-[#FAF8F5] border-[#E2D9CF] text-[#1C1917]'
  }`

  const redirectPath = (location.state as { from?: string })?.from || '/assess'

  const onSubmit = async () => {
    if (!email || !password) return
    if (password.length < 8) {
      setLocalError('Password must be at least 8 characters.')
      return
    }
    setLocalError(null)
    try {
      await handleRegister(email, password)
      setEmail('')
      setPassword('')
      navigate(redirectPath)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch {
      // Error is handled by context
    }
  }

  const displayError = localError || registerError

  return (
    <div className="max-w-md mx-auto px-4 py-16 space-y-8">
      <Link
        to="/"
        className="inline-flex items-center space-x-1.5 text-xs font-bold text-[#44403C] dark:text-[#D6D3D1] hover:text-[#1C1917] transition-colors no-underline"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Home</span>
      </Link>

      <div className="text-center space-y-3">
        <div className="w-14 h-14 rounded-2xl bg-[#593D2B] mx-auto flex items-center justify-center shadow-xs">
          <UserPlus className="w-7 h-7 text-[#8BA470]" />
        </div>
        <div>
          <h1 className="text-2xl font-bold font-serif text-[#382416] dark:text-[#F9F7F2]">
            Create your account
          </h1>
          <p className="text-sm font-medium text-[#44403C] dark:text-[#D6D3D1] mt-1">
            Join BunaVision — for coffee producers, cooperatives &amp; exporters
          </p>
        </div>
      </div>

      <div className={`p-6 sm:p-8 ${card} space-y-5`}>
        {displayError && (
          <div className="p-3.5 rounded-xl border border-red-300 dark:border-red-900/50 bg-red-50 dark:bg-red-950/20 flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-red-700 dark:text-red-400 shrink-0 mt-0.5" />
            <p className="text-xs font-semibold text-red-900 dark:text-red-300">
              {displayError}
            </p>
          </div>
        )}

        <form
          onSubmit={(e) => {
            e.preventDefault()
            onSubmit()
          }}
          className="space-y-4"
        >
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-[#44403C] dark:text-[#D6D3D1]">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3.5 top-3.5 text-[#44403C] dark:text-[#D6D3D1]" />
              <input
                type="email"
                required
                placeholder="you@washingstation.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                className={`pl-10 ${inputCls}`}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-bold text-[#44403C] dark:text-[#D6D3D1]">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3.5 top-3.5 text-[#44403C] dark:text-[#D6D3D1]" />
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                className={`pl-10 ${inputCls}`}
              />
            </div>
            <p className="text-xs font-medium text-[#44403C] dark:text-[#D6D3D1]">
              Must be at least 8 characters
            </p>
          </div>

          <button
            type="submit"
            disabled={registerLoading || !email || !password}
            className="w-full py-3 rounded-xl bg-[#593D2B] hover:bg-[#483020] text-white text-xs font-bold transition-all shadow-xs flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50"
          >
            {registerLoading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Creating account…</span>
              </>
            ) : (
              <>
                <UserPlus className="w-4 h-4" />
                <span>Create Account</span>
              </>
            )}
          </button>
        </form>

        <p className="text-xs text-center text-[#44403C] dark:text-[#D6D3D1] leading-relaxed">
          By creating an account you acknowledge that BunaVision provides preliminary AI
          screenings only — not official grades.
        </p>

        <div className="pt-2 text-center text-xs font-medium text-[#44403C] dark:text-[#D6D3D1]">
          Already have an account?{' '}
          <Link
            to="/login"
            className="font-bold text-[#593D2B] dark:text-[#A7BF8C] hover:underline"
          >
            Sign in
          </Link>
        </div>
      </div>
    </div>
  )
}
