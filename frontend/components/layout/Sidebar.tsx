"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

const navItems = [
  { href: "/app", label: "Mission Control" },
  { href: "/app/workers", label: "AI Sales Workers" },
  { href: "/app/onboarding", label: "Onboarding" },
  { href: "/app/worker-builder", label: "Worker Builder" },
  { href: "/app/worker-instances", label: "Worker Instances" },
  { href: "/app/worker-runs", label: "Worker Runs" },
  { href: "/app/worker-chains", label: "Worker Chains" },
  { href: "/app/analytics", label: "Workspace Analytics" },
  { href: "/app/creator", label: "Creator Dashboard" },
  { href: "/app/marketplace", label: "Marketplace" },
  { href: "/app/campaigns", label: "Missions" },
  { href: "/app/leads", label: "Leads" },
  { href: "/app/replies", label: "Interested Replies" },
  { href: "/app/meetings", label: "Meeting Pipeline" },
  { href: "/app/integrations", label: "Integrations" },
  { href: "/app/settings/billing", label: "Billing" },
  { href: "/app/admin", label: "Admin" },
  { href: "/app/settings", label: "Settings" }
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden w-64 border-r border-slate-200 bg-white p-4 lg:block">
      <div className="mb-8">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Thorpe Workforce</p>
        <h2 className="mt-1 text-lg font-semibold text-slate-900">Deploy AI Employees</h2>
      </div>
      <nav className="space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={clsx(
              "block rounded-lg px-3 py-2 text-sm font-medium transition",
              pathname === item.href || pathname.startsWith(`${item.href}/`)
                ? "bg-brand-50 text-brand-600"
                : "text-slate-700 hover:bg-slate-100"
            )}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
