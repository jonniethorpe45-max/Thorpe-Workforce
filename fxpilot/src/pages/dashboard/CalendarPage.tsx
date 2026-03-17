import { Card } from '@/components/ui/card'

const events = [
  { time: '08:30', impact: 'High', title: 'US CPI y/y', pair: 'USD' },
  { time: '10:00', impact: 'Medium', title: 'ECB President Speech', pair: 'EUR' },
  { time: '14:00', impact: 'High', title: 'FOMC Minutes', pair: 'USD' },
  { time: '23:50', impact: 'Medium', title: 'Japan Trade Balance', pair: 'JPY' },
]

export function CalendarPage() {
  return (
    <Card>
      <h1 className="text-xl font-semibold">Economic Calendar</h1>
      <p className="mt-1 text-sm text-muted-foreground">Upcoming events likely to impact forex volatility.</p>
      <div className="mt-4 space-y-2">
        {events.map((event) => (
          <div key={`${event.time}-${event.title}`} className="grid grid-cols-4 gap-2 rounded-md border border-border p-3 text-sm">
            <span className="font-mono">{event.time}</span>
            <span>{event.impact}</span>
            <span className="col-span-2">{event.title} ({event.pair})</span>
          </div>
        ))}
      </div>
    </Card>
  )
}
