import type { ReactNode } from "react";

export function TableShell({ children }: { children: ReactNode }) {
  return <div className="card overflow-hidden border border-slate-200/50 bg-slate-900/50">{children}</div>;
}
