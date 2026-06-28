import { useState } from 'react'

import { LoadingState } from '@/components/LoadingState'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useAnalysis } from '@/hooks/useMarketData'
import { MAJOR_PAIRS, type MajorPair } from '@/types/trading'

export function AIAnalysisPage() {
  const [pair, setPair] = useState<MajorPair>('EUR_USD')
  const analysis = useAnalysis(pair)

  return (
    <div className="space-y-4">
      <Card className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">AI Analysis</h1>
          <p className="text-sm text-muted-foreground">Technical + Sentiment + Risk agent consensus</p>
        </div>
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
      </Card>
      {analysis.isLoading ? (
        <LoadingState />
      ) : analysis.data ? (
        <>
          <div className="grid gap-3 sm:grid-cols-3">
            {analysis.data.agents.map((agent) => (
              <Card key={agent.name}>
                <p className="text-sm text-muted-foreground">{agent.name} Agent</p>
                <div className="mt-2 flex items-center gap-2">
                  <Badge>{agent.vote}</Badge>
                  <span className="text-sm text-muted-foreground">{Math.round(agent.confidence * 100)}%</span>
                </div>
                <p className="mt-3 text-sm">{agent.reasoning}</p>
              </Card>
            ))}
          </div>
          <Card>
            <p className="text-sm text-muted-foreground">Consensus</p>
            <p className="mt-1 text-2xl font-semibold">{analysis.data.finalAction}</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Score {Math.round(analysis.data.consensusScore * 100)} · Confidence {Math.round(analysis.data.confidence * 100)}%
            </p>
            <div className="mt-4 grid gap-2 text-sm sm:grid-cols-3">
              <p>Entry: {analysis.data.suggestion.entry.toFixed(5)}</p>
              <p>SL: {analysis.data.suggestion.stopLoss.toFixed(5)}</p>
              <p>TP: {analysis.data.suggestion.takeProfit.toFixed(5)}</p>
            </div>
          </Card>
        </>
      ) : (
        <Card>Unable to load AI analysis.</Card>
      )}
    </div>
  )
}
