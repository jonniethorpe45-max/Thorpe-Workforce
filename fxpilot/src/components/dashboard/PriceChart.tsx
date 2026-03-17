import { format } from 'date-fns'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { Card, CardTitle } from '@/components/ui/card'
import type { CandlePoint, MajorPair } from '@/types/trading'

interface PriceChartProps {
  pair: MajorPair
  candles: CandlePoint[]
}

export function PriceChart({ pair, candles }: PriceChartProps) {
  return (
    <Card className="h-[360px]">
      <CardTitle>{pair.replace('_', '/')} — 5m Candles</CardTitle>
      <div className="mt-4 h-[290px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={candles}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              dataKey="time"
              tickFormatter={(value: string) => format(new Date(value), 'HH:mm')}
              stroke="hsl(var(--muted-foreground))"
            />
            <YAxis stroke="hsl(var(--muted-foreground))" domain={['auto', 'auto']} />
            <Tooltip
              labelFormatter={(value) => format(new Date(value), 'MMM dd HH:mm')}
              contentStyle={{
                border: '1px solid hsl(var(--border))',
                borderRadius: 8,
                background: 'hsl(var(--card))',
              }}
            />
            <Line type="monotone" dataKey="close" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}
