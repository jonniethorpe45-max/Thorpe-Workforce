import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { Card } from '@/components/ui/card'
import { usePerformanceStats } from '@/hooks/useMarketData'

export function PerformancePage() {
  const stats = usePerformanceStats()
  const chartData = stats.equity.map((value, index) => ({ step: index + 1, equity: value }))

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-4">
        <Card>
          <p className="text-sm text-muted-foreground">Win Rate</p>
          <p className="mt-2 text-2xl font-semibold">{stats.winRate.toFixed(1)}%</p>
        </Card>
        <Card>
          <p className="text-sm text-muted-foreground">Avg Return</p>
          <p className="mt-2 text-2xl font-semibold">{stats.avgReturn.toFixed(2)}</p>
        </Card>
        <Card>
          <p className="text-sm text-muted-foreground">Best Trade</p>
          <p className="mt-2 text-2xl font-semibold text-success">{stats.best.toFixed(2)}</p>
        </Card>
        <Card>
          <p className="text-sm text-muted-foreground">Worst Trade</p>
          <p className="mt-2 text-2xl font-semibold text-danger">{stats.worst.toFixed(2)}</p>
        </Card>
      </div>
      <Card className="h-[360px]">
        <h1 className="text-lg font-semibold">Equity Curve</h1>
        <div className="mt-4 h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <XAxis dataKey="step" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="equity" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  )
}
