import { useMemo } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { useAuth } from '@/providers/AuthProvider'
import {
  fetchAccountSummary,
  fetchAnalysis,
  fetchAutopilotLogs,
  fetchCandles,
  fetchNewsSentiment,
  fetchPositions,
  fetchPrices,
  fetchTradeHistory,
  fetchWatchlist,
  runAutopilotCycle,
  runBacktest,
  toggleWatchlist,
} from '@/services/api'
import { MAJOR_PAIRS, type MajorPair } from '@/types/trading'

export function usePrices() {
  return useQuery({
    queryKey: ['prices'],
    queryFn: () => fetchPrices([...MAJOR_PAIRS]),
    refetchInterval: 5000,
  })
}

export function useCandles(pair: MajorPair) {
  return useQuery({
    queryKey: ['candles', pair],
    queryFn: () => fetchCandles(pair),
    refetchInterval: 5000,
  })
}

export function useAccountSummary() {
  return useQuery({
    queryKey: ['account-summary'],
    queryFn: fetchAccountSummary,
    refetchInterval: 15_000,
  })
}

export function usePositions() {
  return useQuery({
    queryKey: ['positions'],
    queryFn: fetchPositions,
    refetchInterval: 5000,
  })
}

export function useTradeHistory() {
  return useQuery({
    queryKey: ['trade-history'],
    queryFn: fetchTradeHistory,
  })
}

export function useAnalysis(pair: MajorPair) {
  return useQuery({
    queryKey: ['analysis', pair],
    queryFn: () => fetchAnalysis(pair),
  })
}

export function useWatchlist() {
  const { session } = useAuth()
  const client = useQueryClient()

  const query = useQuery({
    queryKey: ['watchlist', session?.user.id],
    queryFn: () => fetchWatchlist(session),
  })

  const mutation = useMutation({
    mutationFn: async (pair: MajorPair) => {
      const current = query.data ?? []
      const active = !current.includes(pair)
      return toggleWatchlist(session, pair, active)
    },
    onMutate: async (pair) => {
      await client.cancelQueries({ queryKey: ['watchlist', session?.user.id] })
      const previous = client.getQueryData<MajorPair[]>(['watchlist', session?.user.id]) ?? []
      const exists = previous.includes(pair)
      const optimistic = exists ? previous.filter((entry) => entry !== pair) : [...previous, pair]
      client.setQueryData(['watchlist', session?.user.id], optimistic)
      return { previous }
    },
    onError: (_error, _pair, context) => {
      if (context?.previous) {
        client.setQueryData(['watchlist', session?.user.id], context.previous)
      }
    },
    onSettled: () => {
      void client.invalidateQueries({ queryKey: ['watchlist', session?.user.id] })
    },
  })

  return {
    ...query,
    toggle: mutation.mutateAsync,
    updating: mutation.isPending,
  }
}

export function useAutopilotLogs() {
  return useQuery({
    queryKey: ['autopilot-logs'],
    queryFn: fetchAutopilotLogs,
    refetchInterval: 15_000,
  })
}

export function useRunAutopilotCycle() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: runAutopilotCycle,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['autopilot-logs'] })
    },
  })
}

export function useRunBacktest() {
  return useMutation({
    mutationFn: runBacktest,
  })
}

export function useNewsSentiment(pair: MajorPair) {
  return useQuery({
    queryKey: ['news-sentiment', pair],
    queryFn: () => fetchNewsSentiment(pair),
    refetchInterval: 60_000,
  })
}

export function usePerformanceStats() {
  const { data } = useTradeHistory()

  return useMemo(() => {
    const trades = data ?? []
    const closed = trades.filter((trade) => trade.status === 'CLOSED')
    const wins = closed.filter((trade) => trade.profitLoss > 0).length
    const losses = closed.length - wins
    const winRate = closed.length ? (wins / closed.length) * 100 : 0
    const avgReturn = closed.length
      ? closed.reduce((sum, trade) => sum + trade.profitLoss, 0) / closed.length
      : 0
    const best = closed.reduce((bestTrade, trade) => Math.max(bestTrade, trade.profitLoss), 0)
    const worst = closed.reduce((worstTrade, trade) => Math.min(worstTrade, trade.profitLoss), 0)
    const equity = closed.reduce<number[]>((series, trade, index) => {
      const prev = index === 0 ? 100_000 : series[index - 1]
      series.push(prev + trade.profitLoss)
      return series
    }, [])

    return { trades: closed.length, wins, losses, winRate, avgReturn, best, worst, equity }
  }, [data])
}
