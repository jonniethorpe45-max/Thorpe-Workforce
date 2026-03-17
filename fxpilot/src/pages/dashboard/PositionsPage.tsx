import { toast } from 'sonner'

import { LoadingState } from '@/components/LoadingState'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { closeTrade } from '@/services/api'
import { usePositions } from '@/hooks/useMarketData'
import { formatCurrency, formatNumber } from '@/lib/utils'

export function PositionsPage() {
  const positions = usePositions()

  async function close(positionId: string) {
    try {
      await closeTrade(positionId)
      toast.success('Position closed.')
      void positions.refetch()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Unable to close position')
    }
  }

  if (positions.isLoading) {
    return <LoadingState label="Loading open positions..." />
  }

  return (
    <Card>
      <h1 className="text-xl font-semibold">Open Positions</h1>
      <div className="mt-4 space-y-3">
        {(positions.data ?? []).map((position) => (
          <div key={position.id} className="rounded-md border border-border p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="font-mono text-sm">{position.pair.replace('_', '/')}</p>
              <p className={position.pnl >= 0 ? 'text-success' : 'text-danger'}>{formatCurrency(position.pnl)}</p>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              {position.direction} {position.units.toLocaleString()} @ {formatNumber(position.openPrice)}
            </p>
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              <Input type="number" step="0.00001" defaultValue={position.stopLoss ?? undefined} aria-label="Stop loss" />
              <Input type="number" step="0.00001" defaultValue={position.takeProfit ?? undefined} aria-label="Take profit" />
            </div>
            <div className="mt-3 flex gap-2">
              <Button size="sm" variant="outline" onClick={() => toast.success('SL/TP updated (foundation placeholder).')}>
                Update SL/TP
              </Button>
              <Button size="sm" variant="danger" onClick={() => void close(position.id)}>
                Close
              </Button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
