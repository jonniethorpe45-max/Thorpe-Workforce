import { Navigate, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from '@/components/ProtectedRoute'
import { DashboardLayout } from '@/layouts/DashboardLayout'
import { AuthPage } from '@/pages/AuthPage'
import { LandingPage } from '@/pages/LandingPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { AIAnalysisPage } from '@/pages/dashboard/AIAnalysisPage'
import { AlertsPage } from '@/pages/dashboard/AlertsPage'
import { AuditPage } from '@/pages/dashboard/AuditPage'
import { AutopilotPage } from '@/pages/dashboard/AutopilotPage'
import { BacktesterPage } from '@/pages/dashboard/BacktesterPage'
import { CalendarPage } from '@/pages/dashboard/CalendarPage'
import { CopyTradingPage } from '@/pages/dashboard/CopyTradingPage'
import { DashboardHomePage } from '@/pages/dashboard/DashboardHomePage'
import { HistoryPage } from '@/pages/dashboard/HistoryPage'
import { PaperTradingPage } from '@/pages/dashboard/PaperTradingPage'
import { PerformancePage } from '@/pages/dashboard/PerformancePage'
import { PositionsPage } from '@/pages/dashboard/PositionsPage'
import { RiskPage } from '@/pages/dashboard/RiskPage'
import { SentimentPage } from '@/pages/dashboard/SentimentPage'
import { SettingsPage } from '@/pages/dashboard/SettingsPage'
import { TradePage } from '@/pages/dashboard/TradePage'

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/auth" element={<AuthPage />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<DashboardLayout />}>
          <Route index element={<DashboardHomePage />} />
          <Route path="trade" element={<TradePage />} />
          <Route path="ai" element={<AIAnalysisPage />} />
          <Route path="autopilot" element={<AutopilotPage />} />
          <Route path="positions" element={<PositionsPage />} />
          <Route path="history" element={<HistoryPage />} />
          <Route path="risk" element={<RiskPage />} />
          <Route path="backtester" element={<BacktesterPage />} />
          <Route path="alerts" element={<AlertsPage />} />
          <Route path="paper" element={<PaperTradingPage />} />
          <Route path="copy" element={<CopyTradingPage />} />
          <Route path="sentiment" element={<SentimentPage />} />
          <Route path="calendar" element={<CalendarPage />} />
          <Route path="performance" element={<PerformancePage />} />
          <Route path="audit" element={<AuditPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
