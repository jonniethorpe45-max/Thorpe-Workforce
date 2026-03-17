import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.50.3'

import { corsHeaders, json } from '../_shared/cors.ts'

const SUPABASE_URL = Deno.env.get('SUPABASE_URL') ?? ''
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''

Deno.serve(async (request) => {
  if (request.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const payload = await request.json()
    const token = request.headers.get('x-webhook-token') ?? payload.token
    if (!token) return json({ error: 'Missing webhook token' }, 400)

    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    const { data: webhook, error } = await supabase
      .from('tradingview_webhooks')
      .select('user_id, enabled, default_units')
      .eq('webhook_token', token)
      .single()

    if (error || !webhook || !webhook.enabled) {
      return json({ accepted: false, reason: 'Webhook not enabled' }, 403)
    }

    const direction = String(payload.direction ?? 'BUY').toUpperCase()
    const pair = String(payload.pair ?? 'EUR_USD').toUpperCase()

    await supabase.from('autopilot_logs').insert({
      user_id: webhook.user_id,
      pair,
      action: direction,
      reason: 'TradingView webhook signal',
      units: Number(payload.units ?? webhook.default_units),
      executed: false,
    })

    return json({ accepted: true })
  } catch (error) {
    return json({ error: error instanceof Error ? error.message : 'Unexpected error' }, 500)
  }
})
