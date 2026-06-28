import type { Session } from '@supabase/supabase-js'

import { isSupabaseConfigured } from '@/lib/env'
import { supabase } from '@/lib/supabase'
import {
  getMockAnalysis,
  getMockAutopilotLogs,
  getMockCandles,
  getMockPositions,
  getMockPrices,
  getMockSummary,
  getMockTradeHistory,
} from '@/services/mockData'
import {
  MAJOR_PAIRS,
  type AccountSummary,
  type AnalysisResult,
  type AutopilotLog,
  type CandlePoint,
  type MajorPair,
  type Position,
  type PriceTick,
  type TradeRecord,
} from '@/types/trading'

interface OandaProxyPayload {
  action:
    | 'prices'
    | 'candles'
    | 'account'
    | 'positions'
    | 'trades'
    | 'order'
    | 'close-position'
    | 'close-trade'
  pair?: MajorPair
  pairs?: MajorPair[]
  order?: Record<string, unknown>
}

async function invokeFunction<T>(name: string, body: object) {
  if (!isSupabaseConfigured || !supabase) {
    throw new Error('Supabase is not configured. Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.')
  }

  const { data, error } = await supabase.functions.invoke<T>(name, {
    body: body as Record<string, unknown>,
  })
  if (error) {
    if (error.message.includes('429')) {
      throw new Error('Broker rate limit reached. FXPilot is automatically backing off and retrying.')
    }
    throw new Error(error.message)
  }
  if (!data) {
    throw new Error(`No response from edge function: ${name}`)
  }
  return data
}

export async function getSession() {
  if (!isSupabaseConfigured) {
    const value = window.localStorage.getItem('fxpilot-mock-session')
    if (!value) return null
    return JSON.parse(value) as Session
  }
  if (!supabase) {
    return null
  }
  const { data } = await supabase.auth.getSession()
  return data.session
}

export async function signIn(email: string, password: string) {
  if (!isSupabaseConfigured) {
    if (!email || password.length < 8) {
      throw new Error('Invalid credentials.')
    }
    const now = new Date().toISOString()
    const mockSession = {
      access_token: 'mock-token',
      token_type: 'bearer',
      expires_in: 3600,
      expires_at: Date.now() + 3600,
      refresh_token: 'mock-refresh',
      user: {
        id: crypto.randomUUID(),
        email,
        aud: 'authenticated',
        role: 'authenticated',
        created_at: now,
        app_metadata: {},
        user_metadata: {},
      },
    } as Session
    window.localStorage.setItem('fxpilot-mock-session', JSON.stringify(mockSession))
    return
  }
  if (!supabase) {
    throw new Error('Supabase auth not configured.')
  }
  const { error } = await supabase.auth.signInWithPassword({ email, password })
  if (error) {
    throw new Error(error.message)
  }
}

export async function signUp(email: string, password: string) {
  if (!isSupabaseConfigured) {
    if (!email || password.length < 8) {
      throw new Error('Invalid sign-up payload.')
    }
    return
  }
  if (!supabase) {
    throw new Error('Supabase auth not configured.')
  }
  const { error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      emailRedirectTo: `${window.location.origin}/auth`,
    },
  })
  if (error) {
    throw new Error(error.message)
  }
}

export async function signOut() {
  if (!isSupabaseConfigured) {
    window.localStorage.removeItem('fxpilot-mock-session')
    return
  }
  if (!supabase) {
    return
  }
  const { error } = await supabase.auth.signOut()
  if (error) {
    throw new Error(error.message)
  }
}

export async function fetchPrices(pairs: MajorPair[]): Promise<PriceTick[]> {
  if (!isSupabaseConfigured) {
    return getMockPrices(pairs)
  }
  const result = await invokeFunction<{ prices: PriceTick[] }>('oanda-proxy', { action: 'prices', pairs })
  return result.prices
}

export async function fetchCandles(pair: MajorPair): Promise<CandlePoint[]> {
  if (!isSupabaseConfigured) {
    return getMockCandles(pair)
  }
  const result = await invokeFunction<{ candles: CandlePoint[] }>('oanda-proxy', {
    action: 'candles',
    pair,
    granularity: 'M5',
    count: 120,
  })
  return result.candles
}

export async function fetchAccountSummary(): Promise<AccountSummary> {
  if (!isSupabaseConfigured) {
    return getMockSummary()
  }
  const result = await invokeFunction<{ account: AccountSummary }>('oanda-proxy', { action: 'account' })
  return result.account
}

export async function fetchPositions(): Promise<Position[]> {
  if (!isSupabaseConfigured) {
    return getMockPositions()
  }
  const result = await invokeFunction<{ positions: Position[] }>('oanda-proxy', { action: 'positions' })
  return result.positions
}

export async function fetchTradeHistory(): Promise<TradeRecord[]> {
  if (!isSupabaseConfigured) {
    return getMockTradeHistory()
  }
  if (!supabase) {
    throw new Error('Supabase not configured.')
  }

  const { data, error } = await supabase
    .from('trade_history')
    .select('*')
    .order('close_time', { ascending: false })
    .limit(200)

  if (error) {
    throw new Error(error.message)
  }

  return (data ?? []).map((row) => ({
    id: String(row.id),
    pair: row.pair as MajorPair,
    direction: row.direction,
    units: row.units,
    openPrice: row.open_price,
    closePrice: row.close_price,
    openTime: row.open_time,
    closeTime: row.close_time,
    profitLoss: row.profit_loss,
    status: row.status,
    stopLoss: row.stop_loss,
    takeProfit: row.take_profit,
    beastMode: Boolean(row.beast_mode),
  }))
}

export async function placeOrder(payload: OandaProxyPayload) {
  if (!isSupabaseConfigured) {
    return { accepted: true, tradeId: `paper-${Date.now()}` }
  }
  return invokeFunction('oanda-proxy', payload)
}

export async function closeTrade(tradeId: string) {
  if (!isSupabaseConfigured) {
    return { closed: true }
  }
  return invokeFunction('oanda-proxy', { action: 'close-trade', tradeId })
}

export async function fetchWatchlist(session: Session | null): Promise<MajorPair[]> {
  if (!session || !isSupabaseConfigured) {
    const saved = window.localStorage.getItem('fxpilot-watchlist')
    return (saved ? (JSON.parse(saved) as MajorPair[]) : ['EUR_USD', 'GBP_USD']).filter((pair) =>
      MAJOR_PAIRS.includes(pair as MajorPair),
    ) as MajorPair[]
  }
  if (!supabase) {
    throw new Error('Supabase not configured.')
  }

  const { data, error } = await supabase.from('watchlists').select('pair')
  if (error) {
    throw new Error(error.message)
  }
  return (data ?? []).map((row) => row.pair as MajorPair)
}

export async function toggleWatchlist(session: Session | null, pair: MajorPair, active: boolean) {
  if (!session || !isSupabaseConfigured || !supabase) {
    const current = await fetchWatchlist(null)
    const next = active ? [...new Set([...current, pair])] : current.filter((entry) => entry !== pair)
    window.localStorage.setItem('fxpilot-watchlist', JSON.stringify(next))
    return next
  }

  if (active) {
    const { error } = await supabase.from('watchlists').upsert({ pair, user_id: session.user.id })
    if (error) throw new Error(error.message)
  } else {
    const { error } = await supabase.from('watchlists').delete().eq('pair', pair)
    if (error) throw new Error(error.message)
  }

  return fetchWatchlist(session)
}

export async function fetchAnalysis(pair: MajorPair): Promise<AnalysisResult> {
  if (!isSupabaseConfigured) {
    return getMockAnalysis(pair)
  }
  const result = await invokeFunction<AnalysisResult>('ai-analysis', { pair })
  return result
}

export async function fetchAutopilotLogs(): Promise<AutopilotLog[]> {
  if (!isSupabaseConfigured || !supabase) {
    return getMockAutopilotLogs()
  }
  const { data, error } = await supabase
    .from('autopilot_logs')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(50)

  if (error) throw new Error(error.message)

  return (data ?? []).map((row) => ({
    id: String(row.id),
    pair: row.pair as MajorPair,
    action: row.action,
    reason: row.reason,
    units: row.units,
    executed: row.executed,
    error: row.error,
    createdAt: row.created_at,
  }))
}

export async function runAutopilotCycle() {
  if (!isSupabaseConfigured) {
    return { ok: true, cyclesExecuted: 1 }
  }
  return invokeFunction('autopilot', { action: 'run' })
}

export async function runBacktest(payload: {
  pair: MajorPair
  timeframe: string
  from: string
  to: string
}): Promise<{ winRate: number; totalPnL: number; maxDrawdown: number; sharpeRatio: number }> {
  if (!isSupabaseConfigured) {
    return {
      winRate: 57.2,
      totalPnL: 1880.12,
      maxDrawdown: 4.8,
      sharpeRatio: 1.22,
    }
  }
  return invokeFunction('autopilot', { action: 'backtest', ...payload })
}

export interface SentimentHeadline {
  id: string
  pair: MajorPair
  headline: string
  sentiment: number
  source: string
  publishedAt: string
}

export async function fetchNewsSentiment(pair: MajorPair): Promise<SentimentHeadline[]> {
  if (!isSupabaseConfigured) {
    return [
      {
        id: '1',
        pair,
        headline: 'Dollar edges lower as inflation expectations cool.',
        sentiment: 0.22,
        source: 'Reuters',
        publishedAt: new Date().toISOString(),
      },
      {
        id: '2',
        pair,
        headline: 'Central bank commentary hints at extended tightening pause.',
        sentiment: 0.61,
        source: 'Bloomberg',
        publishedAt: new Date().toISOString(),
      },
    ]
  }
  const result = await invokeFunction<{ headlines: SentimentHeadline[] }>('news-sentiment', { pair })
  return result.headlines
}

export interface UserSettingsPayload {
  displayName: string
  brokerApiKey: string
  brokerAccountId: string
  isPractice: boolean
  telegramBotToken: string
  telegramChatId: string
  telegramEnabled: boolean
  webhookToken: string
  webhookEnabled: boolean
}

export async function saveUserSettings(session: Session | null, payload: UserSettingsPayload) {
  if (!session || !isSupabaseConfigured || !supabase) {
    window.localStorage.setItem('fxpilot-settings', JSON.stringify(payload))
    return
  }

  const userId = session.user.id

  const [{ error: profileError }, { error: brokerError }, { error: telegramError }, { error: webhookError }] =
    await Promise.all([
      supabase.from('profiles').upsert({ user_id: userId, display_name: payload.displayName }),
      supabase.from('broker_credentials').upsert({
        user_id: userId,
        api_key: payload.brokerApiKey,
        account_id: payload.brokerAccountId,
        broker_name: 'oanda',
        is_practice: payload.isPractice,
      }),
      supabase.from('telegram_settings').upsert({
        user_id: userId,
        bot_token: payload.telegramBotToken,
        chat_id: payload.telegramChatId,
        enabled: payload.telegramEnabled,
      }),
      supabase.from('tradingview_webhooks').upsert({
        user_id: userId,
        webhook_token: payload.webhookToken,
        enabled: payload.webhookEnabled,
      }),
    ])

  if (profileError || brokerError || telegramError || webhookError) {
    throw new Error(
      profileError?.message ??
        brokerError?.message ??
        telegramError?.message ??
        webhookError?.message ??
        'Unable to save settings',
    )
  }
}
