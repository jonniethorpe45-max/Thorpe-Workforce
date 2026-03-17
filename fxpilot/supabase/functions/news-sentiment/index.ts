import { corsHeaders, json } from '../_shared/cors.ts'

Deno.serve(async (request) => {
  if (request.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { pair } = (await request.json()) as { pair?: string }
    const selectedPair = pair ?? 'EUR_USD'
    const now = new Date().toISOString()

    return json({
      headlines: [
        {
          id: crypto.randomUUID(),
          pair: selectedPair,
          headline: 'Central bank policy divergence supports intraday momentum.',
          sentiment: 0.63,
          source: 'MarketWire',
          publishedAt: now,
        },
        {
          id: crypto.randomUUID(),
          pair: selectedPair,
          headline: 'Risk-off flows cap upside after mixed employment print.',
          sentiment: -0.31,
          source: 'FXStreet',
          publishedAt: now,
        },
      ],
    })
  } catch (error) {
    return json({ error: error instanceof Error ? error.message : 'Unexpected error' }, 500)
  }
})
