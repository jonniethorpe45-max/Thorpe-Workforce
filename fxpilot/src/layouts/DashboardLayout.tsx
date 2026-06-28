import {
  Bell,
  Bot,
  CalendarClock,
  ChartCandlestick,
  ClipboardList,
  Copy,
  Gauge,
  History,
  LayoutDashboard,
  LogOut,
  Newspaper,
  Radar,
  Settings,
  ShieldAlert,
  TestTube2,
} from 'lucide-react'
import { NavLink, Outlet } from 'react-router-dom'

import { ConnectionStatus } from '@/components/dashboard/ConnectionStatus'
import { Button } from '@/components/ui/button'
import { usePrices } from '@/hooks/useMarketData'
import { useAuth } from '@/providers/AuthProvider'

const navItems = [
  { to: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { to: '/dashboard/trade', label: 'Trade', icon: ChartCandlestick },
  { to: '/dashboard/ai', label: 'AI Analysis', icon: Bot },
  { to: '/dashboard/autopilot', label: 'Autopilot', icon: Radar },
  { to: '/dashboard/positions', label: 'Positions', icon: ShieldAlert },
  { to: '/dashboard/history', label: 'History', icon: History },
  { to: '/dashboard/risk', label: 'Risk', icon: ShieldAlert },
  { to: '/dashboard/backtester', label: 'Backtester', icon: TestTube2 },
  { to: '/dashboard/alerts', label: 'Alerts', icon: Bell },
  { to: '/dashboard/paper', label: 'Paper', icon: ClipboardList },
  { to: '/dashboard/copy', label: 'Copy', icon: Copy },
  { to: '/dashboard/sentiment', label: 'Sentiment', icon: Newspaper },
  { to: '/dashboard/calendar', label: 'Calendar', icon: CalendarClock },
  { to: '/dashboard/performance', label: 'Performance', icon: Gauge },
  { to: '/dashboard/audit', label: 'Audit', icon: ClipboardList },
  { to: '/dashboard/settings', label: 'Settings', icon: Settings },
]

export function DashboardLayout() {
  const { logout, user } = useAuth()
  const prices = usePrices()

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex max-w-[1400px]">
        <aside className="hidden min-h-screen w-64 border-r border-border p-4 lg:block">
          <p className="text-xl font-semibold text-foreground">FXPilot</p>
          <p className="mt-1 text-xs text-muted-foreground">{user?.email}</p>
          <nav className="mt-6 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/dashboard'}
                  className={({ isActive }) =>
                    `flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors ${isActive ? 'bg-primary/15 text-primary' : 'text-muted-foreground hover:bg-secondary hover:text-foreground'}`
                  }
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </NavLink>
              )
            })}
          </nav>
        </aside>

        <main className="flex-1 p-4 sm:p-6">
          <header className="mb-6 flex items-center justify-between rounded-xl border border-border bg-card px-4 py-3">
            <div>
              <p className="text-sm text-muted-foreground">Broker Connection</p>
              <ConnectionStatus connected={!prices.isError} />
            </div>
            <Button variant="outline" onClick={() => void logout()}>
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </Button>
          </header>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
