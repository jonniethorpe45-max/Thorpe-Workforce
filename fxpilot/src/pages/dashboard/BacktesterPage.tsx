import { useState } from 'react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useRunBacktest } from '@/hooks/useMarketData'
import { MAJOR_PAIRS, type MajorPair } from '@/types/trading'

export function BacktesterPage() {
  const [pair, setPair] = useState<MajorPair>('EUR_USD')
  const [timeframe, setTimeframe] = useState('M15')
  const [from, setFrom] = useState('2025-01-01')
  const [to, setTo] = useState('2025-12-31')
  const backtest = useRunBacktest()

  async function run() {
    try {
      await backtest.mutateAsync({ pair, timeframe, from, to })
      toast.success('Backtest finished.')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Backtest failed')
    }
  }

  return (
    <Card>
      <h1 className="text-xl font-semibold">Backtester</h1>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Pair</Label>
          <Select value={pair} onValueChange={(value) => setPair(value as MajorPair)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {MAJOR_PAIRS.map((item) => (
                <SelectItem key={item} value={item}>
                  {item.replace('_', '/')}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Timeframe</Label>
          <Select value={timeframe} onValueChange={setTimeframe}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="M5">M5</SelectItem>
              <SelectItem value="M15">M15</SelectItem>
              <SelectItem value="H1">H1</SelectItem>
              <SelectItem value="H4">H4</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>From</Label>
          <Input type="date" value={from} onChange={(event) => setFrom(event.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>To</Label>
          <Input type="date" value={to} onChange={(event) => setTo(event.target.value)} />
        </div>
      </div>
      <Button className="mt-4" onClick={() => void run()} disabled={backtest.isPending}>
        Run Backtest
      </Button>

      {backtest.data ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-4">
          <Card>
            <p className="text-sm text-muted-foreground">Win Rate</p>
            <p className="font-mono text-xl">{backtest.data.winRate}%</p>
          </Card>
          <Card>
            <p className="text-sm text-muted-foreground">Total P&amp;L</p>
            <p className="font-mono text-xl">{backtest.data.totalPnL}</p>
          </Card>
          <Card>
            <p className="text-sm text-muted-foreground">Max Drawdown</p>
            <p className="font-mono text-xl">{backtest.data.maxDrawdown}%</p>
          </Card>
          <Card>
            <p className="text-sm text-muted-foreground">Sharpe</p>
            <p className="font-mono text-xl">{backtest.data.sharpeRatio}</p>
          </Card>
        </div>
      ) : null}
    </Card>
  )
}
