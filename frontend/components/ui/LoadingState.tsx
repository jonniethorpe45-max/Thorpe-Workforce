export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="card p-6">
      <div className="space-y-3">
        <div className="skeleton h-2 w-40" />
        <div className="skeleton h-2 w-64" />
        <div className="skeleton h-2 w-52" />
      </div>
      <p className="mt-4 text-sm text-slate-600">{label}</p>
    </div>
  );
}
