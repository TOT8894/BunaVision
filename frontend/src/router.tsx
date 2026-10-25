import { createBrowserRouter } from 'react-router'
import { AppShell } from './components/layout/AppShell'
import { HomePage } from './features/home/HomePage'
import { AssessPage } from './features/upload/AssessPage'
import { HistoryPage } from './features/history/HistoryPage'
import { ReportPage } from './features/assessment/ReportPage'
import { AdminDashboard } from './features/admin/AdminDashboard'
import { ContactsPage } from './features/contacts/ContactsPage'
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
      {
        path: 'admin',
        element: <AdminDashboard />,
      },
      {
        path: 'contacts',
        element: <ContactsPage />,
      },
      {
        path: 'login',
        element: <LoginPage />,
      },
      {
        path: 'register',
        element: <RegisterPage />,
      },
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
])
