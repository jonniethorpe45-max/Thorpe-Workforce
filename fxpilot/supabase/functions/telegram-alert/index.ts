import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.50.3'

import { corsHeaders, json } from '../_shared/cors.ts'

const SUPABASE_URL = Deno.env.get('SUPABASE_URL') ?? ''
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''

Deno.serve(async (request) => {
  if (request.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const token = request.headers.get('Authorization')?.replace('Bearer ', '')
    if (!token) return json({ error: 'Unauthorized' }, 401)

    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    const { data: userData, error: userError } = await supabase.auth.getUser(token)
    if (userError || !userData.user) return json({ error: 'Unauthorized' }, 401)

    const { message } = (await request.json()) as { message: string }
    const { data: settings, error } = await supabase
      .from('telegram_settings')
      .select('bot_token, chat_id, enabled')
      .eq('user_id', userData.user.id)
      .single()

    if (error || !settings || !settings.enabled) {
      return json({ sent: false, reason: 'Telegram disabled' })
    }

    const response = await fetch(`https://api.telegram.org/bot${settings.bot_token}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: settings.chat_id,
        text: message,
      }),
    })

    const payload = await response.json()
    return json({ sent: response.ok, payload }, response.ok ? 200 : 400)
  } catch (error) {
    return json({ error: error instanceof Error ? error.message : 'Unexpected error' }, 500)
  }
})
