import { Badge } from '@/components/ui/badge'

export function ConnectionStatus({ connected }: { connected: boolean }) {
  return (
    <Badge className={connected ? 'border-success/40 bg-success/15 text-success' : 'border-danger/40 bg-danger/15 text-danger'}>
      {connected ? 'Live' : 'Disconnected'}
    </Badge>
  )
}
