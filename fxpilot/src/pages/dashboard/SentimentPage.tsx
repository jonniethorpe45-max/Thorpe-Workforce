import { useState } from 'react'

import { Card } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useNewsSentiment } from '@/hooks/useMarketData'
import { MAJOR_PAIRS, type MajorPair } from '@/types/trading'

export function SentimentPage() {
  const [pair, setPair] = useState<MajorPair>('EUR_USD')
  const sentiment = useNewsSentiment(pair)

  return (
    <Card>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">News Sentiment</h1>
        <Select value={pair} onValueChange={(value) => setPair(value as MajorPair)}>
          <SelectTrigger className="w-48">
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
      <div className="mt-4 space-y-3">
        {(sentiment.data ?? []).map((headline) => (
          <div key={headline.id} className="rounded-md border border-border p-3">
            <p className="font-medium">{headline.headline}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {headline.source} · {new Date(headline.publishedAt).toLocaleString()} · score {headline.sentiment.toFixed(2)}
            </p>
          </div>
        ))}
      </div>
    </Card>
  )
}
