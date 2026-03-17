import { format, parseISO } from 'date-fns'
import { useMemo } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { Card } from '@/components/ui/card'
import { usePerformanceStats, useTradeHistory } from '@/hooks/useMarketData'
import { calculateDrawdown } from '@/utils/trading'

export function RiskPage() {
  const history = useTradeHistory()
  const performance = usePerformanceStats()

  const daily = useMemo(() => {
    const grouped = new Map<string, number>()
    ;(history.data ?? []).forEach((trade) => {
      if (!trade.closeTime) return
      const key = format(parseISO(trade.closeTime), 'MM-dd')
      grouped.set(key, (grouped.get(key) ?? 0) + trade.profitLoss)
    })
    return [...grouped.entries()].map(([day, pnl]) => ({ day, pnl }))
  }, [history.data])

  const drawdown = calculateDrawdown(performance.equity)
  const marginUtilization = 28.4

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-3">
        <Card>
          <p className="text-sm text-muted-foreground">Max Drawdown</p>
          <p className="mt-2 font-mono text-2xl text-danger">{drawdown}%</p>
        </Card>
        <Card>
          <p className="text-sm text-muted-foreground">Margin Utilization</p>
          <p className="mt-2 font-mono text-2xl">{marginUtilization}%</p>
        </Card>
        <Card>
          <p className="text-sm text-muted-foreground">Risk Per Trade</p>
          <p className="mt-2 font-mono text-2xl">1.00%</p>
        </Card>
      </div>
      <Card className="h-[360px]">
        <h1 className="text-lg font-semibold">Daily P&amp;L</h1>
        <div className="mt-4 h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={daily}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="day" stroke="hsl(var(--muted-foreground))" />
              <YAxis stroke="hsl(var(--muted-foreground))" />
              <Tooltip />
              <Bar dataKey="pnl" fill="hsl(var(--primary))" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  )
}
