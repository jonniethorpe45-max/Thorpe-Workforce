import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { z } from 'zod'

import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { useAutopilotLogs, useRunAutopilotCycle } from '@/hooks/useMarketData'

const settingsSchema = z.object({
  pairs: z.string().min(3),
  intervalMinutes: z.number().min(1),
  riskLevel: z.enum(['conservative', 'moderate', 'aggressive', 'max']),
  baseUnits: z.number().min(100),
  maxUnits: z.number().min(100),
  dailyLossLimit: z.number().min(100),
  maxOpenTrades: z.number().min(1),
  cooldownMinutes: z.number().min(1),
  beastMode: z.boolean(),
  adaptiveSizing: z.boolean(),
  paperMode: z.boolean(),
})

type SettingsValues = z.infer<typeof settingsSchema>

export function AutopilotPage() {
  const form = useForm<SettingsValues>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      pairs: 'EUR_USD,GBP_USD,USD_JPY',
      intervalMinutes: 5,
      riskLevel: 'moderate',
      baseUnits: 4000,
      maxUnits: 20000,
      dailyLossLimit: 1200,
      maxOpenTrades: 4,
      cooldownMinutes: 10,
      beastMode: false,
      adaptiveSizing: true,
      paperMode: true,
    },
  })
  const logs = useAutopilotLogs()
  const runCycle = useRunAutopilotCycle()

  const values = form.watch()

  function saveSettings() {
    toast.success('Autopilot settings saved locally. Persist via Supabase table in production.')
  }

  async function run() {
    try {
      await runCycle.mutateAsync()
      toast.success('Autopilot cycle executed.')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Cycle failed')
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <h1 className="text-xl font-semibold">Autopilot</h1>
        <p className="text-sm text-muted-foreground">Automated trading with consensus, filters, and safeguards.</p>
        <form
          className="mt-4 grid gap-4 sm:grid-cols-2"
          onSubmit={form.handleSubmit(() => {
            saveSettings()
          })}
        >
          <div className="space-y-2 sm:col-span-2">
            <Label>Pairs (comma separated)</Label>
            <Input {...form.register('pairs')} />
          </div>
          <div className="space-y-2">
            <Label>Interval (minutes)</Label>
            <Input type="number" {...form.register('intervalMinutes', { valueAsNumber: true })} />
          </div>
          <div className="space-y-2">
            <Label>Risk level</Label>
            <Select value={values.riskLevel} onValueChange={(value) => form.setValue('riskLevel', value as SettingsValues['riskLevel'])}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="conservative">Conservative</SelectItem>
                <SelectItem value="moderate">Moderate</SelectItem>
                <SelectItem value="aggressive">Aggressive</SelectItem>
                <SelectItem value="max">Max</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Base units</Label>
            <Input type="number" {...form.register('baseUnits', { valueAsNumber: true })} />
          </div>
          <div className="space-y-2">
            <Label>Max units</Label>
            <Input type="number" {...form.register('maxUnits', { valueAsNumber: true })} />
          </div>
          <div className="space-y-2">
            <Label>Daily loss limit</Label>
            <Input type="number" {...form.register('dailyLossLimit', { valueAsNumber: true })} />
          </div>
          <div className="space-y-2">
            <Label>Max open trades</Label>
            <Input type="number" {...form.register('maxOpenTrades', { valueAsNumber: true })} />
          </div>
          <div className="space-y-2">
            <Label>Cooldown minutes</Label>
            <Input type="number" {...form.register('cooldownMinutes', { valueAsNumber: true })} />
          </div>
          <div className="space-y-3 rounded-md border border-border p-3">
            <div className="flex items-center justify-between">
              <Label>Beast mode</Label>
              <Switch checked={values.beastMode} onCheckedChange={(checked) => form.setValue('beastMode', checked)} />
            </div>
            <div className="flex items-center justify-between">
              <Label>Adaptive sizing</Label>
              <Switch checked={values.adaptiveSizing} onCheckedChange={(checked) => form.setValue('adaptiveSizing', checked)} />
            </div>
            <div className="flex items-center justify-between">
              <Label>Paper mode</Label>
              <Switch checked={values.paperMode} onCheckedChange={(checked) => form.setValue('paperMode', checked)} />
            </div>
          </div>
          <div className="sm:col-span-2 flex flex-wrap gap-2">
            <Button type="submit">Save settings</Button>
            <Button type="button" variant="outline" onClick={() => void run()} disabled={runCycle.isPending}>
              Run cycle now
            </Button>
          </div>
        </form>
      </Card>

      <Card>
        <h2 className="text-lg font-semibold">Recent Autopilot Logs</h2>
        <div className="mt-3 space-y-2 text-sm">
          {(logs.data ?? []).map((log) => (
            <div key={log.id} className="rounded-md border border-border p-3">
              <p className="font-medium">
                {log.pair.replace('_', '/')} · {log.action} · {log.units.toLocaleString()} units
              </p>
              <p className="text-muted-foreground">{log.reason}</p>
              {log.error ? <p className="text-danger">{log.error}</p> : null}
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
