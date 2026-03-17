import { Star } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { formatNumber } from '@/lib/utils'
import type { PriceTick } from '@/types/trading'

interface PairCardProps {
  price: PriceTick
  selected: boolean
  watched: boolean
  onSelect: () => void
  onToggleWatch: () => void
}

export function PairCard({ price, selected, watched, onSelect, onToggleWatch }: PairCardProps) {
  return (
    <Card
      className={`cursor-pointer p-4 transition-colors ${selected ? 'border-primary bg-primary/10' : ''}`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
    >
      <div className="flex items-start justify-between">
        <p className="font-mono text-sm text-muted-foreground">{price.pair.replace('_', '/')}</p>
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0"
          onClick={(event) => {
            event.stopPropagation()
            onToggleWatch()
          }}
          aria-label="Toggle watchlist"
        >
          <Star className={`h-4 w-4 ${watched ? 'fill-primary text-primary' : ''}`} />
        </Button>
      </div>
      <p className="mt-2 font-mono text-xl text-foreground">{formatNumber(price.bid)}</p>
      <p className="mt-1 text-xs text-muted-foreground">Ask {formatNumber(price.ask)} · Spread {formatNumber(price.spread, 5)}</p>
    </Card>
  )
}
