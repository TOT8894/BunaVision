import { createBrowserRouter } from 'react-router'
import { AppShell } from './components/layout/AppShell'
import { ProtectedRoute } from './components/common/ProtectedRoute'
import { AdminRoute } from './components/common/AdminRoute'
import { HomePage } from './features/home/HomePage'
import { AssessPage } from './features/upload/AssessPage'
import { HistoryPage } from './features/history/HistoryPage'
import { ReportPage } from './features/assessment/ReportPage'
import { AdminDashboard } from './features/admin/AdminDashboard'
import { LoginPage } from './features/auth/LoginPage'
import { RegisterPage } from './features/auth/RegisterPage'
import { NotFoundPage } from './features/not-found/NotFoundPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: 'login',
        element: <LoginPage />,
      },
      {
        path: 'register',
        element: <RegisterPage />,
      },
      // Signed-in user routes
      {
        element: <ProtectedRoute />,
        children: [
          {
            path: 'assess',
            element: <AssessPage />,
          },
          {
            path: 'assessments',
            element: <HistoryPage />,
          },
          {
            path: 'assessments/:id',
            element: <ReportPage />,
          },
        ],
      },
      // Admin-only route
      {
        element: <AdminRoute />,
        children: [
          {
            path: 'admin',
            element: <AdminDashboard />,
          },
        ],
      },
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
])
