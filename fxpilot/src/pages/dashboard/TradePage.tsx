import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { z } from 'zod'

import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { placeOrder } from '@/services/api'
import { MAJOR_PAIRS } from '@/types/trading'
import { calculatePositionSize } from '@/utils/trading'

const tradeSchema = z.object({
  pair: z.enum(MAJOR_PAIRS),
  orderType: z.enum(['market', 'limit']),
  direction: z.enum(['BUY', 'SELL']),
  units: z.number().min(1),
  limitPrice: z.number().optional(),
  stopLoss: z.number().optional(),
  takeProfit: z.number().optional(),
  trailingStop: z.number().optional(),
  riskPercent: z.number().min(0.1).max(5),
  accountBalance: z.number().min(100),
  stopLossPips: z.number().min(1),
  paperMode: z.boolean(),
})

type TradeFormValues = z.infer<typeof tradeSchema>

export function TradePage() {
  const [confirmOpen, setConfirmOpen] = useState(false)
  const form = useForm<TradeFormValues>({
    resolver: zodResolver(tradeSchema),
    defaultValues: {
      pair: 'EUR_USD',
      orderType: 'market',
      direction: 'BUY',
      units: 5000,
      riskPercent: 1,
      accountBalance: 100000,
      stopLossPips: 20,
      paperMode: true,
    },
  })

  const values = form.watch()
  const suggestedUnits = calculatePositionSize({
    accountBalance: values.accountBalance,
    riskPercent: values.riskPercent,
    stopLossPips: values.stopLossPips,
    pipValuePerUnit: 0.0001,
    maxUnits: 150_000,
  })

  async function submit(valuesToSubmit: TradeFormValues) {
    try {
      await placeOrder({
        action: 'order',
        order: {
          ...valuesToSubmit,
          mode: valuesToSubmit.paperMode ? 'paper' : 'live',
        },
      })
      toast.success(valuesToSubmit.paperMode ? 'Paper order placed.' : 'Live order submitted.')
      form.reset({ ...valuesToSubmit, units: suggestedUnits })
      setConfirmOpen(false)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Order failed')
    }
  }

  return (
    <Card className="space-y-4">
      <h1 className="text-xl font-semibold">Trade Panel</h1>
      <form className="grid gap-4 sm:grid-cols-2" onSubmit={form.handleSubmit(() => setConfirmOpen(true))}>
        <div className="space-y-2">
          <Label>Pair</Label>
          <Select value={values.pair} onValueChange={(value) => form.setValue('pair', value as TradeFormValues['pair'])}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {MAJOR_PAIRS.map((pair) => (
                <SelectItem key={pair} value={pair}>
                  {pair.replace('_', '/')}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Order Type</Label>
          <Select value={values.orderType} onValueChange={(value) => form.setValue('orderType', value as 'market' | 'limit')}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="market">Market</SelectItem>
              <SelectItem value="limit">Limit</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Direction</Label>
          <Select value={values.direction} onValueChange={(value) => form.setValue('direction', value as 'BUY' | 'SELL')}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="BUY">BUY</SelectItem>
              <SelectItem value="SELL">SELL</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="units">Units</Label>
          <Input id="units" type="number" {...form.register('units', { valueAsNumber: true })} />
          <p className="text-xs text-muted-foreground">Suggested size: {suggestedUnits.toLocaleString()}</p>
        </div>
        <div className="space-y-2">
          <Label htmlFor="riskPercent">Risk %</Label>
          <Input id="riskPercent" type="number" step="0.1" {...form.register('riskPercent', { valueAsNumber: true })} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="stopLossPips">Stop Loss (pips)</Label>
          <Input id="stopLossPips" type="number" {...form.register('stopLossPips', { valueAsNumber: true })} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="stopLoss">Stop Loss (price)</Label>
          <Input
            id="stopLoss"
            type="number"
            step="0.00001"
            {...form.register('stopLoss', {
              setValueAs: (value) => (value === '' ? undefined : Number(value)),
            })}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="takeProfit">Take Profit</Label>
          <Input
            id="takeProfit"
            type="number"
            step="0.00001"
            {...form.register('takeProfit', {
              setValueAs: (value) => (value === '' ? undefined : Number(value)),
            })}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="trailingStop">Trailing Stop</Label>
          <Input
            id="trailingStop"
            type="number"
            step="0.1"
            {...form.register('trailingStop', {
              setValueAs: (value) => (value === '' ? undefined : Number(value)),
            })}
          />
        </div>
        <div className="flex items-center justify-between rounded-md border border-border px-3 py-2">
          <div>
            <Label>Paper mode</Label>
            <p className="text-xs text-muted-foreground">Disable to submit live orders.</p>
          </div>
          <Switch checked={values.paperMode} onCheckedChange={(checked) => form.setValue('paperMode', checked)} />
        </div>
        <Button className="sm:col-span-2" type="submit">
          Review order
        </Button>
      </form>

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogTitle>Confirm trade execution</DialogTitle>
          <DialogDescription>
            Ensure stop-loss and take-profit levels are set. Trading involves substantial risk.
          </DialogDescription>
          <div className="rounded-md border border-border p-3 text-sm">
            <p>{values.direction} {values.units.toLocaleString()} units on {values.pair.replace('_', '/')}</p>
            <p className="text-muted-foreground">Mode: {values.paperMode ? 'Paper' : 'Live'}</p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmOpen(false)}>Cancel</Button>
            <Button onClick={form.handleSubmit(submit)} disabled={form.formState.isSubmitting}>
              Confirm
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
