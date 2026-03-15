import type { ReactNode } from "react";

type Props = {
  label: string;
  value: string | number;
  hint?: string;
  icon?: ReactNode;
};

export function StatCard({ label, value, hint, icon }: Props) {
  return (
    <div className="card group p-4">
      <div className="flex items-start justify-between gap-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
        {icon ? (
          <div className="rounded-lg border border-cyan-400/30 bg-cyan-400/10 p-2 text-cyan-300 transition group-hover:scale-105">{icon}</div>
        ) : null}
      </div>
      <p className="mt-3 text-2xl font-semibold text-slate-900">{value}</p>
      {hint ? <p className="mt-1 text-xs text-slate-500">{hint}</p> : null}
    </div>
  );
}
