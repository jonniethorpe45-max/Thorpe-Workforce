import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

const traders = [
  { id: '1', name: 'MacroHawk', winRate: 62.1, pnl: 12_340, trades: 248 },
  { id: '2', name: 'LondonFlow', winRate: 57.3, pnl: 8_290, trades: 183 },
  { id: '3', name: 'TokyoBreakout', winRate: 54.2, pnl: 5_450, trades: 160 },
]

export function CopyTradingPage() {
  const [following, setFollowing] = useState<Record<string, boolean>>({})

  return (
    <Card>
      <h1 className="text-xl font-semibold">Copy Trading Marketplace</h1>
      <p className="mt-1 text-sm text-muted-foreground">Follow public traders and set your copy multiplier.</p>
      <div className="mt-4 space-y-3">
        {traders.map((trader) => (
          <div key={trader.id} className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-border p-4">
            <div>
              <p className="font-semibold">{trader.name}</p>
              <p className="text-sm text-muted-foreground">
                Win rate {trader.winRate}% · P&amp;L ${trader.pnl.toLocaleString()} · {trader.trades} trades
              </p>
            </div>
            <Button
              variant={following[trader.id] ? 'outline' : 'default'}
              onClick={() => setFollowing((prev) => ({ ...prev, [trader.id]: !prev[trader.id] }))}
            >
              {following[trader.id] ? 'Unfollow' : 'Follow'}
            </Button>
          </div>
        ))}
      </div>
    </Card>
  )
}
