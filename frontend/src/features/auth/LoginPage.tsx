import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router'
import {
  ArrowLeft,
  Mail,
  Lock,
  RefreshCw,
  LogIn,
  Layers,
  AlertTriangle,
  User,
  Shield,
  Sparkles,
} from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import { useAuth } from '../../contexts/AuthContext'

export function LoginPage() {
  const { theme } = useTheme()
  const { handleLogin, loginError, loginLoading, loginAsDemo } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

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
    try {
      await handleLogin(email, password)
      setEmail('')
      setPassword('')
      navigate(redirectPath)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch {
      // Error is handled by context
    }
  }

  const handleDemoSignIn = (role: 'user' | 'admin') => {
    loginAsDemo(role)
    if (role === 'admin') {
      navigate('/admin')
    } else {
      navigate(redirectPath)
    }
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="max-w-md mx-auto px-4 py-16 space-y-8 animate-fade-in-up">
      <Link
        to="/"
        className="inline-flex items-center space-x-1.5 text-xs font-bold text-[#44403C] dark:text-[#D6D3D1] hover:text-[#1C1917] transition-colors no-underline"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Home</span>
      </Link>

      <div className="text-center space-y-3">
        <div className="w-14 h-14 rounded-2xl bg-[#593D2B] mx-auto flex items-center justify-center shadow-xs">
          <Layers className="w-7 h-7 text-[#8BA470]" />
        </div>
        <div>
          <h1 className="text-2xl font-bold font-serif text-[#382416] dark:text-[#F9F7F2]">
            Welcome back
          </h1>
          <p className="text-sm font-medium text-[#44403C] dark:text-[#D6D3D1] mt-1">
            Sign in to your BunaVision account
          </p>
        </div>
      </div>

      <div className={`p-6 sm:p-8 ${card} space-y-5`}>
        {loginError && (
          <div className="p-3.5 rounded-xl border border-red-300 dark:border-red-900/50 bg-red-50 dark:bg-red-950/20 flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-red-700 dark:text-red-400 shrink-0 mt-0.5" />
            <p className="text-xs font-semibold text-red-900 dark:text-red-300">
              {loginError}
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
                placeholder="name@washingstation.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
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
                className={`pl-10 ${inputCls}`}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loginLoading}
            className="w-full py-3 rounded-xl bg-[#593D2B] hover:bg-[#483020] text-white text-xs font-bold transition-all shadow-xs flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50"
          >
            {loginLoading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <LogIn className="w-4 h-4" />
                <span>Sign In to BunaVision</span>
              </>
            )}
          </button>
        </form>

        <div className="pt-2 text-center text-xs font-medium text-[#44403C] dark:text-[#D6D3D1]">
          Don't have an account yet?{' '}
          <Link
            to="/register"
            className="font-bold text-[#593D2B] dark:text-[#A7BF8C] hover:underline"
          >
            Create account
          </Link>
        </div>

        {/* Demo Users Section for UI/UX Evaluation */}
        <div className="pt-4 border-t border-[#E2D9CF] dark:border-[#382E26] space-y-3">
          <div className="flex items-center gap-1.5 justify-center text-xs font-bold text-[#593D2B] dark:text-[#A7BF8C] uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Interactive Demo Accounts</span>
          </div>
          <p className="text-xs text-center text-[#44403C] dark:text-[#D6D3D1]">
            One-click sign in with preloaded sample data for testing the UI/UX. Easily deletable at any time.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
            <button
              type="button"
              onClick={() => handleDemoSignIn('user')}
              className="px-3 py-2.5 rounded-xl border border-[#8BA470]/40 bg-[#8BA470]/10 hover:bg-[#8BA470]/20 text-[#3A5228] dark:text-[#B5CF97] text-xs font-bold flex items-center justify-center gap-1.5 transition-colors cursor-pointer shadow-2xs"
            >
              <User className="w-3.5 h-3.5" />
              <span>Demo User (Producer)</span>
            </button>
            <button
              type="button"
              onClick={() => handleDemoSignIn('admin')}
              className="px-3 py-2.5 rounded-xl border border-[#593D2B]/30 bg-[#593D2B]/10 hover:bg-[#593D2B]/20 text-[#382416] dark:text-[#D6D3D1] text-xs font-bold flex items-center justify-center gap-1.5 transition-colors cursor-pointer shadow-2xs"
            >
              <Shield className="w-3.5 h-3.5 text-[#593D2B] dark:text-[#8BA470]" />
              <span>Demo Admin (Inspector)</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
