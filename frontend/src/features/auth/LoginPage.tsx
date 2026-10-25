import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { ArrowLeft, Mail, Lock, RefreshCw, LogIn, Layers } from 'lucide-react'
import { AlertTriangle } from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import { useAuth } from '../../contexts/AuthContext'

export function LoginPage() {
  const { theme } = useTheme()
  const { handleLogin, loginError, loginLoading } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const card = `rounded-2xl border ${
    theme === 'dark' ? 'bg-[#231F1C] border-[#382E26]' : 'bg-white border-[#E8E0D5]'
  }`
  const inputCls = `w-full px-3 py-2 rounded-xl text-sm border focus:outline-none focus:ring-2 focus:ring-[#8BA470] ${
    theme === 'dark'
      ? 'bg-[#181513] border-[#382E26] text-[#F9F7F2]'
      : 'bg-stone-50 border-[#E8E0D5] text-[#24211D]'
  }`

  const onSubmit = async () => {
    if (!email || !password) return
    try {
      await handleLogin(email, password)
      setEmail('')
      setPassword('')
      navigate('/assess')
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch {
      // Error is handled by context
    }
  }

  return (
    <div className="max-w-md mx-auto px-4 py-16 space-y-8">
      <Link
        to="/"
        className="flex items-center space-x-1.5 text-xs text-[#5A544C] hover:text-[#593D2B] transition-colors no-underline"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Home</span>
      </Link>

      <div className="text-center space-y-3">
        <div className="w-14 h-14 rounded-2xl bg-[#593D2B] mx-auto flex items-center justify-center shadow-lg">
          <Layers className="w-7 h-7 text-[#8BA470]" />
        </div>
        <div>
          <h1 className="text-2xl font-bold font-serif text-[#593D2B] dark:text-[#F9F7F2]">
            Welcome back
          </h1>
          <p className="text-sm text-[#5A544C] dark:text-[#A8A193] mt-1">
            Sign in to your BunaVision account
          </p>
        </div>
      </div>

      <div className={`p-6 space-y-5 ${card}`}>
        {loginError && (
          <div className="flex items-start space-x-2 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-700 dark:text-red-400 text-xs">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{loginError}</span>
          </div>
        )}

        <div className="space-y-1.5">
          <label className="block text-xs font-semibold text-[#5A544C] dark:text-[#A8A193]">
            Email address
          </label>
          <div className="relative">
            <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#7B7569]" />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && onSubmit()}
              placeholder="you@example.com"
              autoComplete="email"
              className={`${inputCls} pl-9`}
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="block text-xs font-semibold text-[#5A544C] dark:text-[#A8A193]">
            Password
          </label>
          <div className="relative">
            <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#7B7569]" />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && onSubmit()}
              placeholder="••••••••"
              autoComplete="current-password"
              className={`${inputCls} pl-9`}
            />
          </div>
        </div>

        <button
          onClick={onSubmit}
          disabled={loginLoading || !email || !password}
          className="w-full py-3 rounded-xl bg-[#593D2B] hover:bg-[#483020] text-white font-semibold text-sm shadow-md transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
        >
          {loginLoading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Signing in…</span>
            </>
          ) : (
            <>
              <LogIn className="w-4 h-4" />
              <span>Sign In</span>
            </>
          )}
        </button>
      </div>

      <p className="text-center text-sm text-[#5A544C] dark:text-[#A8A193]">
        Don't have an account?{' '}
        <Link
          to="/register"
          className="font-semibold text-[#593D2B] dark:text-[#A7BF8C] hover:underline"
        >
          Create one free
        </Link>
      </p>
    </div>
  )
}
