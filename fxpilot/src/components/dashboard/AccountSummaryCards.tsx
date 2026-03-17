import { Card, CardTitle, CardValue } from '@/components/ui/card'
import { formatCurrency } from '@/lib/utils'
import type { AccountSummary } from '@/types/trading'

export function AccountSummaryCards({ summary }: { summary: AccountSummary }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <Card>
        <CardTitle>Balance</CardTitle>
        <CardValue>{formatCurrency(summary.balance)}</CardValue>
      </Card>
      <Card>
        <CardTitle>Unrealized P&amp;L</CardTitle>
        <CardValue className={summary.unrealizedPnL >= 0 ? 'text-success' : 'text-danger'}>
          {formatCurrency(summary.unrealizedPnL)}
        </CardValue>
      </Card>
      <Card>
        <CardTitle>Margin Used</CardTitle>
        <CardValue>{formatCurrency(summary.marginUsed)}</CardValue>
      </Card>
      <Card>
        <CardTitle>Cumulative P&amp;L</CardTitle>
        <CardValue className={summary.cumulativePnL >= 0 ? 'text-success' : 'text-danger'}>
          {formatCurrency(summary.cumulativePnL)}
        </CardValue>
      </Card>
    </div>
  )
}
