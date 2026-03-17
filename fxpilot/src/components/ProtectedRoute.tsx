import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { LoadingState } from '@/components/LoadingState'
import { useAuth } from '@/providers/AuthProvider'

export function ProtectedRoute() {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return <LoadingState label="Checking session..." />
  }

  if (!user) {
    return <Navigate to="/auth" replace state={{ from: location }} />
  }

  return <Outlet />
}
