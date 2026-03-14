import type { ReactNode } from "react";

export function TableShell({ children }: { children: ReactNode }) {
  return <div className="card overflow-hidden">{children}</div>;
}
