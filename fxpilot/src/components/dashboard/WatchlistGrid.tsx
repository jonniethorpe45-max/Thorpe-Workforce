import { Card, CardTitle } from '@/components/ui/card'
import type { MajorPair } from '@/types/trading'

export function WatchlistGrid({ watchlist }: { watchlist: MajorPair[] }) {
  return (
    <Card>
      <CardTitle>Watchlist</CardTitle>
      <div className="mt-4 grid gap-2 sm:grid-cols-2">
        {watchlist.length === 0 ? (
          <p className="text-sm text-muted-foreground">No watched pairs yet.</p>
        ) : (
          watchlist.map((pair) => (
            <div key={pair} className="rounded-md border border-border px-3 py-2 font-mono text-sm">
              {pair.replace('_', '/')}
            </div>
          ))
        )}
      </div>
    </Card>
  )
}
