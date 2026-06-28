import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.50.3'

import { corsHeaders, json } from '../_shared/cors.ts'

const SUPABASE_URL = Deno.env.get('SUPABASE_URL') ?? ''
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''

async function getUserId(supabase: ReturnType<typeof createClient>, token: string) {
  const { data, error } = await supabase.auth.getUser(token)
  if (error || !data.user) return null
  return data.user.id
}

Deno.serve(async (request) => {
  if (request.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const body = await request.json()
    const action = body.action as 'run' | 'status' | 'backtest'
    const token = request.headers.get('Authorization')?.replace('Bearer ', '')
    if (!token) return json({ error: 'Unauthorized' }, 401)

    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    const userId = await getUserId(supabase, token)
    if (!userId) return json({ error: 'Unauthorized' }, 401)

    if (action === 'status') {
      const { data } = await supabase.from('autopilot_settings').select('*').eq('user_id', userId).single()
      return json({ settings: data })
    }

    if (action === 'backtest') {
      // Foundation output. Replace with historical simulation engine in production.
      return json({
        winRate: 55.3,
        totalPnL: 1420.44,
        maxDrawdown: 6.1,
        sharpeRatio: 1.18,
      })
    }

    const { data: settings } = await supabase.from('autopilot_settings').select('*').eq('user_id', userId).single()
    if (!settings) {
      return json({ error: 'Autopilot settings not found' }, 400)
    }

    const pair = (settings.pairs?.[0] as string | undefined) ?? 'EUR_USD'
    const actionVote: 'BUY' | 'SELL' | 'HOLD' = 'HOLD'
    const reason = 'Cycle completed with neutral consensus in foundation mode.'

    await supabase.from('autopilot_logs').insert({
      user_id: userId,
      pair,
      action: actionVote,
      reason,
      units: settings.base_units,
      executed: false,
    })

    await supabase.from('autopilot_reasoning').insert({
      user_id: userId,
      cycle_id: crypto.randomUUID(),
      pair,
      technical_vote: 'HOLD',
      technical_confidence: 0.55,
      technical_reasoning: 'Momentum mixed across short-term frames.',
      sentiment_vote: 'HOLD',
      sentiment_confidence: 0.52,
      sentiment_reasoning: 'No dominant macro catalyst.',
      risk_vote: 'HOLD',
      risk_confidence: 0.6,
      risk_reasoning: 'Volatility elevated versus threshold.',
      final_action: actionVote,
      confidence: 0.56,
      final_reasoning: reason,
      consensus_score: 0.56,
      executed: false,
      units: settings.base_units,
    })

    return json({ ok: true, message: reason })
  } catch (error) {
    return json({ error: error instanceof Error ? error.message : 'Unexpected error' }, 500)
  }
})
