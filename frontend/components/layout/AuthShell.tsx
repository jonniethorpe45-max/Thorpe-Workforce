import type { ReactNode } from "react";
import { BrainCircuit, ShieldCheck, Sparkles, Zap } from "lucide-react";

import { PublicFooter } from "@/components/layout/PublicFooter";
import { PublicNav } from "@/components/layout/PublicNav";

type AuthShellProps = {
  title: string;
  subtitle: string;
  maxWidthClassName?: string;
  children: ReactNode;
};

const highlights = [
  { label: "AI Worker Runs", icon: Zap },
  { label: "Founder OS Automation", icon: Sparkles },
  { label: "Secure Workspace Access", icon: ShieldCheck }
];

export function AuthShell({ title, subtitle, children, maxWidthClassName = "max-w-md" }: AuthShellProps) {
  return (
    <div className="min-h-screen bg-slate-50">
      <PublicNav />
      <main className={`mx-auto flex min-h-[calc(100vh-180px)] w-full items-center px-6 ${maxWidthClassName}`}>
        <div className="grid w-full gap-6 lg:grid-cols-[1.05fr_0.95fr]">
          <section className="card hidden p-6 lg:block">
            <p className="inline-flex items-center gap-2 rounded-full border border-cyan-400/35 bg-cyan-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-200">
              <BrainCircuit className="h-3.5 w-3.5" />
              Thorpe Workforce
            </p>
            <h2 className="mt-4 bg-gradient-to-r from-slate-100 via-cyan-100 to-indigo-300 bg-clip-text text-3xl font-semibold text-transparent">
              AI operating system for modern teams
            </h2>
            <p className="mt-3 text-sm text-slate-600">
              Launch digital workers, automate operations, and manage growth with one command center.
            </p>
            <ul className="mt-6 space-y-3">
              {highlights.map(({ label, icon: Icon }) => (
                <li key={label} className="flex items-center gap-2 rounded-lg border border-slate-200/70 bg-slate-900/45 px-3 py-2 text-sm text-slate-600">
                  <span className="rounded-md border border-cyan-400/30 bg-cyan-400/10 p-1 text-cyan-300">
                    <Icon className="h-3.5 w-3.5" />
                  </span>
                  {label}
                </li>
              ))}
            </ul>
          </section>
          <section className="card w-full space-y-4 p-6">
            <h1 className="text-2xl font-semibold">{title}</h1>
            <p className="text-sm text-slate-600">{subtitle}</p>
            {children}
          </section>
        </div>
      </main>
      <PublicFooter />
    </div>
  );
}
