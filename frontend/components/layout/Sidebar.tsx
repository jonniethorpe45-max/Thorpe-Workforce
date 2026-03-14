"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

const navItems = [
  { href: "/app", label: "Overview" },
  { href: "/app/workers", label: "Workers" },
  { href: "/app/campaigns", label: "Campaigns" },
  { href: "/app/leads", label: "Leads" },
  { href: "/app/replies", label: "Replies" },
  { href: "/app/meetings", label: "Meetings" },
  { href: "/app/integrations", label: "Integrations" },
  { href: "/app/settings", label: "Settings" }
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden w-64 border-r border-slate-200 bg-white p-4 lg:block">
      <div className="mb-8">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Thorpe Workforce</p>
        <h2 className="mt-1 text-lg font-semibold text-slate-900">AI Workforce OS</h2>
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
