import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface AlertItem {
  id: string
  pair: string
  targetPrice: number
  direction: 'above' | 'below'
}

export function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([])
  const [pair, setPair] = useState('EUR_USD')
  const [targetPrice, setTargetPrice] = useState(1.09)
  const [direction, setDirection] = useState<'above' | 'below'>('above')

  function addAlert() {
    setAlerts((prev) => [...prev, { id: crypto.randomUUID(), pair, targetPrice, direction }])
  }

  return (
    <Card>
      <h1 className="text-xl font-semibold">Price Alerts</h1>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div className="space-y-2">
          <Label>Pair</Label>
          <Input value={pair} onChange={(event) => setPair(event.target.value.toUpperCase())} />
        </div>
        <div className="space-y-2">
          <Label>Target Price</Label>
          <Input type="number" step="0.00001" value={targetPrice} onChange={(event) => setTargetPrice(Number(event.target.value))} />
        </div>
        <div className="space-y-2">
          <Label>Direction</Label>
          <select
            value={direction}
            onChange={(event) => setDirection(event.target.value as 'above' | 'below')}
            className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="above">Above</option>
            <option value="below">Below</option>
          </select>
        </div>
      </div>
      <Button className="mt-4" onClick={addAlert}>
        Create Alert
      </Button>

      <div className="mt-4 space-y-2">
        {alerts.map((alert) => (
          <div key={alert.id} className="rounded-md border border-border p-3 text-sm">
            {alert.pair.replace('_', '/')} {alert.direction} {alert.targetPrice}
          </div>
        ))}
      </div>
    </Card>
  )
}
