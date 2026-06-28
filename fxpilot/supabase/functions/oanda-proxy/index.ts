import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.50.3'

import { corsHeaders, json } from '../_shared/cors.ts'

type Action =
  | 'prices'
  | 'candles'
  | 'account'
  | 'positions'
  | 'trades'
  | 'order'
  | 'close-position'
  | 'close-trade'

interface Payload {
  action: Action
  pair?: string
  pairs?: string[]
  order?: Record<string, unknown>
  tradeId?: string
  granularity?: string
  count?: number
}

const SUPABASE_URL = Deno.env.get('SUPABASE_URL') ?? ''
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''

Deno.serve(async (request) => {
  if (request.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const payload = (await request.json()) as Payload
    const authorization = request.headers.get('Authorization')
    const token = authorization?.replace('Bearer ', '')
    if (!token) {
      return json({ error: 'Missing bearer token' }, 401)
    }

    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    const { data: userData, error: userError } = await supabase.auth.getUser(token)
    if (userError || !userData.user) {
      return json({ error: 'Unauthorized' }, 401)
    }

    const { data: creds, error: credsError } = await supabase
      .from('broker_credentials')
      .select('api_key, account_id, is_practice')
      .eq('user_id', userData.user.id)
      .single()

    if (credsError || !creds) {
      return json({ error: 'Broker not connected. Configure OANDA credentials in Settings.' }, 400)
    }

    const domain = creds.is_practice
      ? 'https://api-fxpractice.oanda.com/v3'
      : 'https://api-fxtrade.oanda.com/v3'

    const headers = {
      Authorization: `Bearer ${creds.api_key}`,
      'Content-Type': 'application/json',
    }

    const accountBase = `${domain}/accounts/${creds.account_id}`

    switch (payload.action) {
      case 'prices': {
        const instruments = (payload.pairs ?? ['EUR_USD']).join(',')
        const response = await fetch(`${accountBase}/pricing?instruments=${instruments}`, { headers })
        const data = await response.json()
        return json({ prices: data.prices ?? [] }, response.status)
      }
      case 'candles': {
        const instrument = payload.pair ?? 'EUR_USD'
        const granularity = payload.granularity ?? 'M5'
        const count = payload.count ?? 100
        const response = await fetch(
          `${domain}/instruments/${instrument}/candles?count=${count}&price=M&granularity=${granularity}`,
          { headers },
        )
        const data = await response.json()
        return json(
          {
            candles: (data.candles ?? []).map((item: { time: string; mid: { c: string } }) => ({
              time: item.time,
              close: Number(item.mid.c),
            })),
          },
          response.status,
        )
      }
      case 'account': {
        const response = await fetch(`${accountBase}/summary`, { headers })
        const data = await response.json()
        return json(
          {
            account: {
              balance: Number(data.account?.balance ?? 0),
              unrealizedPnL: Number(data.account?.unrealizedPL ?? 0),
              marginUsed: Number(data.account?.marginUsed ?? 0),
              cumulativePnL: Number(data.account?.pl ?? 0),
            },
          },
          response.status,
        )
      }
      case 'positions': {
        const response = await fetch(`${accountBase}/openPositions`, { headers })
        const data = await response.json()
        return json({ positions: data.positions ?? [] }, response.status)
      }
      case 'trades': {
        const response = await fetch(`${accountBase}/openTrades`, { headers })
        const data = await response.json()
        return json({ trades: data.trades ?? [] }, response.status)
      }
      case 'order': {
        const response = await fetch(`${accountBase}/orders`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ order: payload.order }),
        })
        const data = await response.json()
        return json(data, response.status)
      }
      case 'close-position': {
        const instrument = payload.pair ?? 'EUR_USD'
        const response = await fetch(`${accountBase}/positions/${instrument}/close`, {
          method: 'PUT',
          headers,
          body: JSON.stringify({}),
        })
        const data = await response.json()
        return json(data, response.status)
      }
      case 'close-trade': {
        if (!payload.tradeId) return json({ error: 'tradeId required' }, 400)
        const response = await fetch(`${accountBase}/trades/${payload.tradeId}/close`, {
          method: 'PUT',
          headers,
          body: JSON.stringify({}),
        })
        const data = await response.json()
        return json(data, response.status)
      }
      default:
        return json({ error: 'Unsupported action' }, 400)
    }
  } catch (error) {
    return json({ error: error instanceof Error ? error.message : 'Unexpected error' }, 500)
  }
})
