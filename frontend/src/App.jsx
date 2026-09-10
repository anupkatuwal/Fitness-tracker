import { Suspense, lazy } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import { Spinner } from './components/ui.jsx'
import { useAuth } from './context/AuthContext.jsx'

/* Routes are split so the charting library only loads for the pages that
   actually draw charts. */
const Dashboard = lazy(() => import('./pages/Dashboard.jsx'))
const MacroTracker = lazy(() => import('./pages/MacroTracker.jsx'))
const ExerciseDirectory = lazy(() => import('./pages/ExerciseDirectory.jsx'))
const ExerciseDetail = lazy(() => import('./pages/ExerciseDetail.jsx'))
const PedLibrary = lazy(() => import('./pages/PedLibrary.jsx'))
const PedDetail = lazy(() => import('./pages/PedDetail.jsx'))
const Calculators = lazy(() => import('./pages/Calculators.jsx'))
const Profile = lazy(() => import('./pages/Profile.jsx'))
const Login = lazy(() => import('./pages/Login.jsx'))
const NotFound = lazy(() => import('./pages/NotFound.jsx'))

/** Gates a route behind a session, remembering where the user was headed. */
function RequireAuth({ children }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return <Spinner label="Restoring your session" />
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />
  return children
}

export default function App() {
  return (
    <Suspense fallback={<Spinner label="Loading page" />}>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route
            path="macros"
            element={
              <RequireAuth>
                <MacroTracker />
              </RequireAuth>
            }
          />
          <Route path="exercises" element={<ExerciseDirectory />} />
          <Route path="exercises/:slug" element={<ExerciseDetail />} />
          <Route path="peds" element={<PedLibrary />} />
          <Route path="peds/:slug" element={<PedDetail />} />
          <Route path="calculators" element={<Calculators />} />
          <Route
            path="profile"
            element={
              <RequireAuth>
                <Profile />
              </RequireAuth>
            }
          />
          <Route path="login" element={<Login />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </Suspense>
  )
}
