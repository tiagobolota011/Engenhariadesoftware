import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth/AuthContext'
import { AuthProvider } from './auth/AuthProvider'
import AppShell from './layout/AppShell'
import ComingSoon from './pages/ComingSoon'
import Login from './pages/Login'
import MyRequests from './pages/MyRequests'
import Notifications from './pages/Notifications'
import Prioritization from './pages/Prioritization'
import RequestDetail from './pages/RequestDetail'
import RequestsList from './pages/RequestsList'
import Status from './pages/Status'
import SubmitRequest from './pages/SubmitRequest'

const PLANNED = [
  ['backlog', 'Backlog Management'],
  ['user-stories', 'User Story Generator'],
  ['traceability', 'Traceability'],
  ['roadmap', 'Roadmap'],
  ['dashboard', 'Analytics Dashboard'],
]

function Screens() {
  const { user } = useAuth()
  if (!user) return <Login />
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/requests" element={<RequestsList />} />
        <Route path="/requests/new" element={<SubmitRequest />} />
        <Route path="/requests/:id" element={<RequestDetail />} />
        <Route path="/my-requests" element={<MyRequests />} />
        <Route path="/prioritization" element={<Prioritization />} />
        <Route path="/notifications" element={<Notifications />} />
        {PLANNED.map(([path, title]) => (
          <Route key={path} path={`/${path}`} element={<ComingSoon title={title} />} />
        ))}
        <Route path="*" element={<Navigate to="/requests" replace />} />
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/status" element={<Status />} />
        <Route
          path="*"
          element={
            <AuthProvider>
              <Screens />
            </AuthProvider>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}
