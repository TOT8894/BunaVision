import { Navigate, useLocation, Outlet } from 'react-router'
import { useAuth } from '../../contexts/AuthContext'
import { RefreshCw } from 'lucide-react'

export function ProtectedRoute() {
  const { authToken, authLoading } = useAuth()
  const location = useLocation()

  if (authLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <RefreshCw className="w-8 h-8 animate-spin text-[#8BA470]" />
        <p className="text-sm font-medium text-[#44403C] dark:text-[#D6D3D1]">
          Checking session authentication…
        </p>
      </div>
    )
  }

  if (!authToken) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }

  return <Outlet />
}
