export function LoadingState({ label = 'Loading...' }: { label?: string }) {
  return (
    <div className="flex min-h-[180px] items-center justify-center rounded-xl border border-border bg-card">
      <p className="text-sm text-muted-foreground">{label}</p>
    </div>
  )
}
