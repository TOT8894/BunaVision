import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import { AppShell } from './components/layout/AppShell'
import { HomePage } from './features/home/HomePage'
import { HistoryPage } from './features/history/HistoryPage'
import { AssessmentPage } from './features/assessment/AssessmentPage'
import { NotFoundPage } from './features/not-found/NotFoundPage'
import { UploadPage } from './features/upload/UploadPage'

export function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/assess" element={<UploadPage />} />
          <Route path="/upload" element={<Navigate to="/assess" replace />} />
          <Route path="/assessments" element={<HistoryPage />} />
          <Route path="/assessments/:assessmentId" element={<AssessmentPage />} />
          <Route path="/assessments/:id" element={<AssessmentPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  )
}

export default App
