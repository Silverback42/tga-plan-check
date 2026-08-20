import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { Layout } from './components/Layout'
import { DiffPage } from './pages/DiffPage'
import { ExtractionPage } from './pages/ExtractionPage'
import { ProjectCreatePage } from './pages/ProjectCreatePage'
import { ProjectListPage } from './pages/ProjectListPage'
import { ReportsPage } from './pages/ReportsPage'
import { UploadPage } from './pages/UploadPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<ProjectListPage />} />
          <Route path="/projects/new" element={<ProjectCreatePage />} />
        </Route>

        {/* Projekt-Routen teilen sich das Layout inkl. Projekt-Navigation */}
        <Route path="/projects/:projectId" element={<Layout />}>
          <Route index element={<Navigate to="uploads" replace />} />
          <Route path="uploads" element={<UploadPage />} />
          <Route path="anlagen" element={<ExtractionPage />} />
          <Route path="diff" element={<DiffPage />} />
          <Route path="report" element={<ReportsPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
