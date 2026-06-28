import { corsHeaders, json } from '../_shared/cors.ts'

Deno.serve(async (request) => {
  if (request.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { pair } = (await request.json()) as { pair?: string }
    const selectedPair = pair ?? 'EUR_USD'
    const midpoint = 1.08 + Math.random() * 0.02

    return json({
      pair: selectedPair,
      agents: [
        {
          name: 'Technical',
          vote: 'BUY',
          confidence: 0.71,
          reasoning: 'Trend strength and pullback continuation setup detected.',
        },
        {
          name: 'Sentiment',
          vote: 'HOLD',
          confidence: 0.57,
          reasoning: 'Headline sentiment is mixed with mild USD strength bias.',
        },
        {
          name: 'Risk',
          vote: 'BUY',
          confidence: 0.68,
          reasoning: 'Volatility normalized and projected risk/reward is acceptable.',
        },
      ],
      consensusScore: 0.65,
      finalAction: 'BUY',
      confidence: 0.67,
      suggestion: {
        entry: Number(midpoint.toFixed(5)),
        stopLoss: Number((midpoint * 0.997).toFixed(5)),
        takeProfit: Number((midpoint * 1.004).toFixed(5)),
      },
    })
  } catch (error) {
    return json({ error: error instanceof Error ? error.message : 'Unexpected error' }, 500)
  }
})
