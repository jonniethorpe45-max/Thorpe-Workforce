export const MAJOR_PAIRS = [
  'EUR_USD',
  'GBP_USD',
  'USD_JPY',
  'USD_CHF',
  'AUD_USD',
  'USD_CAD',
  'NZD_USD',
] as const

export type MajorPair = (typeof MAJOR_PAIRS)[number]
export type TradeDirection = 'BUY' | 'SELL'
export type AgentVote = 'BUY' | 'SELL' | 'HOLD'
export type RiskLevel = 'conservative' | 'moderate' | 'aggressive' | 'max'

export interface PriceTick {
  pair: MajorPair
  bid: number
  ask: number
  spread: number
  timestamp: string
}

export interface CandlePoint {
  time: string
  close: number
}

export interface AccountSummary {
  balance: number
  unrealizedPnL: number
  marginUsed: number
  cumulativePnL: number
}

export interface Position {
  id: string
  pair: MajorPair
  direction: TradeDirection
  units: number
  openPrice: number
  currentPrice: number
  pnl: number
  stopLoss: number | null
  takeProfit: number | null
  openedAt: string
}

export interface TradeRecord {
  id: string
  pair: MajorPair
  direction: TradeDirection
  units: number
  openPrice: number
  closePrice: number | null
  openTime: string
  closeTime: string | null
  profitLoss: number
  status: 'OPEN' | 'CLOSED'
  stopLoss: number | null
  takeProfit: number | null
  beastMode: boolean
}

export interface AgentDecision {
  name: string
  vote: AgentVote
  confidence: number
  reasoning: string
}

export interface AnalysisResult {
  pair: MajorPair
  agents: AgentDecision[]
  consensusScore: number
  finalAction: AgentVote
  confidence: number
  suggestion: {
    entry: number
    stopLoss: number
    takeProfit: number
  }
}

export interface AutopilotLog {
  id: string
  pair: MajorPair
  action: AgentVote
  reason: string
  units: number
  executed: boolean
  error: string | null
  createdAt: string
}
