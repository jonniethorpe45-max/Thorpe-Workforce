import { Card } from '@/components/ui/card'
import { useTradeHistory } from '@/hooks/useMarketData'
import { formatCurrency } from '@/lib/utils'

export function PaperTradingPage() {
  const history = useTradeHistory()
  const paperTrades = (history.data ?? []).slice(0, 8)
  const pnl = paperTrades.reduce((sum, trade) => sum + trade.profitLoss, 0)
  const balance = 100_000 + pnl

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <Card>
          <p className="text-sm text-muted-foreground">Virtual Balance</p>
          <p className="mt-2 font-mono text-2xl">{formatCurrency(balance)}</p>
        </Card>
        <Card>
          <p className="text-sm text-muted-foreground">Paper P&amp;L</p>
          <p className={`mt-2 font-mono text-2xl ${pnl >= 0 ? 'text-success' : 'text-danger'}`}>
            {formatCurrency(pnl)}
          </p>
        </Card>
      </div>
      <Card>
        <h1 className="text-xl font-semibold">Recent Paper Trades</h1>
        <div className="mt-3 space-y-2">
          {paperTrades.map((trade) => (
            <div key={trade.id} className="rounded-md border border-border p-3 text-sm">
              {trade.pair.replace('_', '/')} · {trade.direction} · {trade.units.toLocaleString()} units ·{' '}
              <span className={trade.profitLoss >= 0 ? 'text-success' : 'text-danger'}>
                {formatCurrency(trade.profitLoss)}
              </span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
