import { subMinutes } from 'date-fns'

import { calculatePnL } from '@/utils/trading'
import type {
  AccountSummary,
  AnalysisResult,
  AutopilotLog,
  CandlePoint,
  MajorPair,
  Position,
  PriceTick,
  TradeRecord,
} from '@/types/trading'

const basePrices: Record<MajorPair, number> = {
  EUR_USD: 1.0842,
  GBP_USD: 1.2661,
  USD_JPY: 149.21,
  USD_CHF: 0.8921,
  AUD_USD: 0.6612,
  USD_CAD: 1.3512,
  NZD_USD: 0.6094,
}

const cache = new Map<MajorPair, number>(Object.entries(basePrices) as [MajorPair, number][])

function drift(value: number) {
  const change = (Math.random() - 0.5) * value * 0.001
  return Number((value + change).toFixed(5))
}

export function getMockPrices(pairs: MajorPair[]): PriceTick[] {
  return pairs.map((pair) => {
    const price = drift(cache.get(pair) ?? basePrices[pair])
    cache.set(pair, price)

    const spread = Number((price * 0.00008).toFixed(5))
    return {
      pair,
      bid: Number((price - spread / 2).toFixed(5)),
      ask: Number((price + spread / 2).toFixed(5)),
      spread,
      timestamp: new Date().toISOString(),
    }
  })
}

export function getMockCandles(pair: MajorPair): CandlePoint[] {
  const seed = cache.get(pair) ?? basePrices[pair]
  return Array.from({ length: 60 }).map((_, index) => {
    const time = subMinutes(new Date(), 59 - index).toISOString()
    const close = Number((seed + Math.sin(index / 8) * 0.0015 + (Math.random() - 0.5) * 0.0006).toFixed(5))
    return { time, close }
  })
}

export function getMockSummary(): AccountSummary {
  return {
    balance: 127_450.21,
    unrealizedPnL: 312.45,
    marginUsed: 14_870.1,
    cumulativePnL: 8_470.53,
  }
}

export function getMockPositions(): Position[] {
  const reference = getMockPrices(['EUR_USD', 'GBP_USD', 'USD_JPY'])
  return reference.map((price, index) => {
    const direction = index % 2 === 0 ? 'BUY' : 'SELL'
    const units = 10_000 * (index + 1)
    const openPrice = Number((price.bid * (1 + (Math.random() - 0.5) * 0.003)).toFixed(5))
    return {
      id: `mock-pos-${index}`,
      pair: price.pair,
      direction,
      units,
      openPrice,
      currentPrice: price.bid,
      pnl: calculatePnL({
        direction,
        units,
        openPrice,
        currentPrice: price.bid,
      }),
      stopLoss: Number((openPrice * 0.995).toFixed(5)),
      takeProfit: Number((openPrice * 1.01).toFixed(5)),
      openedAt: subMinutes(new Date(), 20 + index * 15).toISOString(),
    }
  })
}

export function getMockTradeHistory(): TradeRecord[] {
  return Array.from({ length: 25 }).map((_, idx) => ({
    id: `trade-${idx}`,
    pair: (Object.keys(basePrices)[idx % 7] as MajorPair) ?? 'EUR_USD',
    direction: idx % 2 === 0 ? 'BUY' : 'SELL',
    units: 5_000 + idx * 400,
    openPrice: 1.07 + idx * 0.0005,
    closePrice: 1.07 + idx * 0.0005 + (Math.random() - 0.5) * 0.003,
    openTime: subMinutes(new Date(), idx * 70 + 120).toISOString(),
    closeTime: subMinutes(new Date(), idx * 70).toISOString(),
    profitLoss: Number(((Math.random() - 0.45) * 320).toFixed(2)),
    status: 'CLOSED',
    stopLoss: 1.06,
    takeProfit: 1.08,
    beastMode: idx % 6 === 0,
  }))
}

export function getMockAnalysis(pair: MajorPair): AnalysisResult {
  const entry = cache.get(pair) ?? basePrices[pair]
  return {
    pair,
    agents: [
      {
        name: 'Technical',
        vote: 'BUY',
        confidence: 0.72,
        reasoning: 'Momentum and trend alignment on 5m/15m frames.',
      },
      {
        name: 'Sentiment',
        vote: 'HOLD',
        confidence: 0.58,
        reasoning: 'Mixed macro headlines with neutral risk appetite.',
      },
      {
        name: 'Risk',
        vote: 'BUY',
        confidence: 0.69,
        reasoning: 'Favorable risk/reward and moderate volatility.',
      },
    ],
    consensusScore: 0.66,
    finalAction: 'BUY',
    confidence: 0.68,
    suggestion: {
      entry,
      stopLoss: Number((entry * 0.997).toFixed(5)),
      takeProfit: Number((entry * 1.004).toFixed(5)),
    },
  }
}

export function getMockAutopilotLogs(): AutopilotLog[] {
  return Array.from({ length: 10 }).map((_, idx) => ({
    id: `log-${idx}`,
    pair: (Object.keys(basePrices)[idx % 7] as MajorPair) ?? 'EUR_USD',
    action: idx % 3 === 0 ? 'HOLD' : idx % 2 === 0 ? 'BUY' : 'SELL',
    reason: 'Consensus threshold met with volatility check passed.',
    units: 5_000 + idx * 500,
    executed: idx % 3 !== 0,
    error: idx % 7 === 0 ? 'Rate-limit backoff triggered once.' : null,
    createdAt: subMinutes(new Date(), idx * 12).toISOString(),
  }))
}
