import { useMemo, useState } from 'react'
import { toast } from 'sonner'

import { AccountSummaryCards } from '@/components/dashboard/AccountSummaryCards'
import { PairCard } from '@/components/dashboard/PairCard'
import { PriceChart } from '@/components/dashboard/PriceChart'
import { WatchlistGrid } from '@/components/dashboard/WatchlistGrid'
import { LoadingState } from '@/components/LoadingState'
import { Card } from '@/components/ui/card'
import { useAccountSummary, useCandles, usePrices, useWatchlist } from '@/hooks/useMarketData'
import { MAJOR_PAIRS, type MajorPair } from '@/types/trading'

export function DashboardHomePage() {
  const [selectedPair, setSelectedPair] = useState<MajorPair>('EUR_USD')
  const prices = usePrices()
  const candles = useCandles(selectedPair)
  const summary = useAccountSummary()
  const watchlist = useWatchlist()

  const sortedPrices = useMemo(() => prices.data ?? [], [prices.data])

  if (prices.isLoading || summary.isLoading) {
    return <LoadingState label="Loading dashboard..." />
  }

  if (prices.isError || summary.isError) {
    return (
      <Card className="text-danger">
        Unable to load broker data. Check credentials in Settings or verify Supabase edge functions are deployed.
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <AccountSummaryCards summary={summary.data!} />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {sortedPrices.map((price) => (
          <PairCard
            key={price.pair}
            price={price}
            selected={selectedPair === price.pair}
            watched={Boolean(watchlist.data?.includes(price.pair))}
            onSelect={() => setSelectedPair(price.pair)}
            onToggleWatch={() =>
              watchlist
                .toggle(price.pair)
                .then(() => toast.success(`${price.pair.replace('_', '/')} watchlist updated`))
                .catch((error: Error) => toast.error(error.message))
            }
          />
        ))}
      </div>
      {candles.data ? <PriceChart pair={selectedPair} candles={candles.data} /> : <LoadingState />}
      <WatchlistGrid watchlist={watchlist.data ?? MAJOR_PAIRS.slice(0, 2)} />
    </div>
  )
}
