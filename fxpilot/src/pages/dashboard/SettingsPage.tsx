import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { z } from 'zod'

import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { useAuth } from '@/providers/AuthProvider'
import { saveUserSettings } from '@/services/api'

const settingsSchema = z.object({
  displayName: z.string().min(2),
  brokerApiKey: z.string().min(10),
  brokerAccountId: z.string().min(4),
  isPractice: z.boolean(),
  telegramBotToken: z.string().min(5),
  telegramChatId: z.string().min(2),
  telegramEnabled: z.boolean(),
  webhookToken: z.string().min(8),
  webhookEnabled: z.boolean(),
})

type SettingsValues = z.infer<typeof settingsSchema>

export function SettingsPage() {
  const { session, user } = useAuth()
  const form = useForm<SettingsValues>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      displayName: user?.email?.split('@')[0] ?? 'Trader',
      brokerApiKey: 'oanda-api-key',
      brokerAccountId: '001-011-1234567-001',
      isPractice: true,
      telegramBotToken: 'telegram-bot-token',
      telegramChatId: '123456',
      telegramEnabled: false,
      webhookToken: 'tv-webhook-token',
      webhookEnabled: false,
    },
  })

  const values = form.watch()

  async function submit(valuesToSave: SettingsValues) {
    try {
      await saveUserSettings(session, valuesToSave)
      toast.success('Settings saved.')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Unable to save settings')
    }
  }

  return (
    <Card>
      <h1 className="text-xl font-semibold">Settings</h1>
      <form className="mt-4 grid gap-4 sm:grid-cols-2" onSubmit={form.handleSubmit(submit)}>
        <div className="space-y-2 sm:col-span-2">
          <Label>Display name</Label>
          <Input {...form.register('displayName')} />
        </div>

        <div className="space-y-2">
          <Label>OANDA API key</Label>
          <Input type="password" {...form.register('brokerApiKey')} />
        </div>
        <div className="space-y-2">
          <Label>OANDA Account ID</Label>
          <Input {...form.register('brokerAccountId')} />
        </div>
        <div className="flex items-center justify-between rounded-md border border-border px-3 py-2 sm:col-span-2">
          <div>
            <Label>Practice mode</Label>
            <p className="text-xs text-muted-foreground">Use OANDA practice endpoint for execution.</p>
          </div>
          <Switch checked={values.isPractice} onCheckedChange={(checked) => form.setValue('isPractice', checked)} />
        </div>

        <div className="space-y-2">
          <Label>Telegram Bot token</Label>
          <Input type="password" {...form.register('telegramBotToken')} />
        </div>
        <div className="space-y-2">
          <Label>Telegram Chat ID</Label>
          <Input {...form.register('telegramChatId')} />
        </div>
        <div className="flex items-center justify-between rounded-md border border-border px-3 py-2 sm:col-span-2">
          <Label>Telegram alerts enabled</Label>
          <Switch
            checked={values.telegramEnabled}
            onCheckedChange={(checked) => form.setValue('telegramEnabled', checked)}
          />
        </div>

        <div className="space-y-2">
          <Label>TradingView webhook token</Label>
          <Input type="password" {...form.register('webhookToken')} />
        </div>
        <div className="flex items-center justify-between rounded-md border border-border px-3 py-2">
          <Label>Webhook enabled</Label>
          <Switch checked={values.webhookEnabled} onCheckedChange={(checked) => form.setValue('webhookEnabled', checked)} />
        </div>
        <Button type="submit" className="sm:col-span-2">
          Save Settings
        </Button>
      </form>
    </Card>
  )
}
