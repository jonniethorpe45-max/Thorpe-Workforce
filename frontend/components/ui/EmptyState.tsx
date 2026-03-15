import type { ReactNode } from "react";

type Props = {
  title: string;
  description: string;
  action?: ReactNode;
};

export function EmptyState({ title, description, action }: Props) {
  return (
    <div className="card p-8 text-center">
      <div className="mx-auto mb-3 h-14 w-14 rounded-2xl border border-cyan-400/35 bg-cyan-400/10 shadow-lg shadow-cyan-900/30" />
      <h3 className="text-base font-semibold text-slate-900">{title}</h3>
      <p className="mt-2 text-sm text-slate-600">{description}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}
