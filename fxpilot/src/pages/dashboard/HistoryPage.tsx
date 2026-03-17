import { useMemo, useState } from 'react'

import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useTradeHistory } from '@/hooks/useMarketData'
import { formatCurrency } from '@/lib/utils'

export function HistoryPage() {
  const [pairFilter, setPairFilter] = useState('')
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const history = useTradeHistory()

  const filtered = useMemo(() => {
    return (history.data ?? []).filter((trade) => {
      const matchesPair = pairFilter ? trade.pair.includes(pairFilter.toUpperCase().replace('/', '_')) : true
      const close = trade.closeTime ? new Date(trade.closeTime).getTime() : 0
      const fromMatch = from ? close >= new Date(from).getTime() : true
      const toMatch = to ? close <= new Date(to).getTime() : true
      return matchesPair && fromMatch && toMatch
    })
  }, [from, history.data, pairFilter, to])

  function exportCsv() {
    const rows = [
      'pair,direction,units,open_price,close_price,profit_loss,open_time,close_time',
      ...filtered.map(
        (trade) =>
          `${trade.pair},${trade.direction},${trade.units},${trade.openPrice},${trade.closePrice ?? ''},${trade.profitLoss},${trade.openTime},${trade.closeTime ?? ''}`,
      ),
    ]
    const blob = new Blob([rows.join('\n')], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = 'fxpilot-trade-history.csv'
    anchor.click()
    URL.revokeObjectURL(url)
  }

  return (
    <Card>
      <h1 className="text-xl font-semibold">Trade History</h1>
      <div className="mt-4 grid gap-2 sm:grid-cols-4">
        <Input placeholder="Pair (EUR/USD)" value={pairFilter} onChange={(event) => setPairFilter(event.target.value)} />
        <Input type="date" value={from} onChange={(event) => setFrom(event.target.value)} />
        <Input type="date" value={to} onChange={(event) => setTo(event.target.value)} />
        <button onClick={exportCsv} className="rounded-md border border-border bg-secondary px-3 py-2 text-sm">
          Export
        </button>
      </div>
      <div className="mt-4 overflow-auto">
        <table className="w-full min-w-[680px] text-sm">
          <thead>
            <tr className="text-left text-muted-foreground">
              <th className="pb-2">Pair</th>
              <th className="pb-2">Direction</th>
              <th className="pb-2">Units</th>
              <th className="pb-2">P&amp;L</th>
              <th className="pb-2">Closed</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((trade) => (
              <tr key={trade.id} className="border-t border-border">
                <td className="py-2 font-mono">{trade.pair.replace('_', '/')}</td>
                <td>{trade.direction}</td>
                <td>{trade.units.toLocaleString()}</td>
                <td className={trade.profitLoss >= 0 ? 'text-success' : 'text-danger'}>
                  {formatCurrency(trade.profitLoss)}
                </td>
                <td>{trade.closeTime ? new Date(trade.closeTime).toLocaleString() : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}
