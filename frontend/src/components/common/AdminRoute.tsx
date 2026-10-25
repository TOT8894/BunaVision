import { Navigate, useLocation, Outlet, Link } from 'react-router'
import { useAuth } from '../../contexts/AuthContext'
import { ShieldAlert, ArrowLeft, RefreshCw } from 'lucide-react'

export function AdminRoute() {
  const { authToken, currentUser, authLoading } = useAuth()
  const location = useLocation()

  if (authLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <RefreshCw className="w-8 h-8 animate-spin text-[#8BA470]" />
        <p className="text-sm font-medium text-[#44403C] dark:text-[#D6D3D1]">
          Validating administrator credentials…
        </p>
      </div>
    )
  }

  if (!authToken) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }

  if (currentUser && currentUser.role !== 'admin') {
    return (
      <div className="max-w-2xl mx-auto px-4 py-24 text-center space-y-6">
        <div className="w-16 h-16 rounded-2xl bg-rose-500/10 dark:bg-rose-500/20 text-rose-700 dark:text-rose-400 flex items-center justify-center mx-auto">
          <ShieldAlert className="w-8 h-8" />
        </div>

        <div className="space-y-2">
          <h1 className="text-3xl font-bold font-serif text-[#382416] dark:text-[#F9F7F2]">
            403 - Administrator Access Required
          </h1>
          <p className="text-sm text-[#44403C] dark:text-[#D6D3D1] max-w-md mx-auto leading-relaxed">
            The telemetry and management console is restricted to system administrators.
            Your account ({currentUser.email}) does not have staff permissions.
          </p>
        </div>

        <div className="pt-2">
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#593D2B] hover:bg-[#483020] text-white text-xs font-bold shadow-xs transition-all no-underline"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to BunaVision Home</span>
          </Link>
        </div>
      </div>
    )
  }

  return <Outlet />
}
