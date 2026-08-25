import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { ThemeProvider } from './theme'
import Layout from './components/Layout.jsx'
import Landing from './pages/Landing.jsx'
import ReportPage from './pages/ReportPage.jsx'
import ReportsList from './pages/ReportsList.jsx'
import ReportDetail from './pages/ReportDetail.jsx'
import Dashboard from './pages/Dashboard.jsx'
import MapPage from './pages/MapPage.jsx'

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/report" element={<ReportPage />} />
            <Route path="/reports" element={<ReportsList />} />
            <Route path="/reports/:id" element={<ReportDetail />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/map" element={<MapPage />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ThemeProvider>
  )
}