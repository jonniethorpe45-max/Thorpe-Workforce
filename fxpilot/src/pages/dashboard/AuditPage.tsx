import { useMemo, useState } from 'react'

import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useAutopilotLogs } from '@/hooks/useMarketData'

export function AuditPage() {
  const [pairFilter, setPairFilter] = useState('')
  const [actionFilter, setActionFilter] = useState('')
  const logs = useAutopilotLogs()

  const filtered = useMemo(() => {
    return (logs.data ?? []).filter((log) => {
      const pairOk = pairFilter ? log.pair.includes(pairFilter.toUpperCase().replace('/', '_')) : true
      const actionOk = actionFilter ? log.action.includes(actionFilter.toUpperCase()) : true
      return pairOk && actionOk
    })
  }, [actionFilter, logs.data, pairFilter])

  return (
    <Card>
      <h1 className="text-xl font-semibold">Autopilot Audit Trail</h1>
      <p className="mt-1 text-sm text-muted-foreground">Reasoning log for every automated trade cycle.</p>
      <div className="mt-4 grid gap-2 sm:grid-cols-2">
        <Input value={pairFilter} onChange={(event) => setPairFilter(event.target.value)} placeholder="Filter pair" />
        <Input value={actionFilter} onChange={(event) => setActionFilter(event.target.value)} placeholder="Filter action (BUY/SELL/HOLD)" />
      </div>
      <div className="mt-4 space-y-2">
        {filtered.map((log) => (
          <div key={log.id} className="rounded-md border border-border p-3 text-sm">
            <p className="font-medium">
              {log.pair.replace('_', '/')} · {log.action} · executed: {log.executed ? 'yes' : 'no'}
            </p>
            <p className="text-muted-foreground">{log.reason}</p>
            <p className="text-xs text-muted-foreground">{new Date(log.createdAt).toLocaleString()}</p>
          </div>
        ))}
      </div>
    </Card>
  )
}
