"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ComponentType } from "react";
import clsx from "clsx";
import {
  BarChart3,
  BriefcaseBusiness,
  ChevronDown,
  ChevronRight,
  Compass,
  Cpu,
  Crown,
  Layers3,
  Rocket,
  Settings,
  Shield,
  Sparkles,
  Store,
  UserCog,
  Users,
  Wrench
} from "lucide-react";

type NavItem = {
  href: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
};

type NavGroup = {
  id: string;
  label: string;
  items: NavItem[];
};

const navGroups: NavGroup[] = [
  {
    id: "core",
    label: "Command Center",
    items: [
      { href: "/app", label: "Mission Control", icon: Rocket },
      { href: "/app/onboarding", label: "Onboarding", icon: Compass },
      { href: "/app/analytics", label: "Workspace Analytics", icon: BarChart3 }
    ]
  },
  {
    id: "workers",
    label: "Worker Stack",
    items: [
      { href: "/app/workers", label: "AI Workers", icon: Cpu },
      { href: "/app/worker-builder", label: "Worker Builder", icon: Wrench },
      { href: "/app/worker-instances", label: "Worker Instances", icon: Layers3 },
      { href: "/app/worker-runs", label: "Worker Runs", icon: Sparkles },
      { href: "/app/worker-chains", label: "Worker Chains", icon: BriefcaseBusiness },
      { href: "/app/founder-os", label: "Founder OS", icon: Crown },
      { href: "/app/founder-os/reports", label: "Founder Reports", icon: Shield }
    ]
  },
  {
    id: "growth",
    label: "Growth + Pipeline",
    items: [
      { href: "/app/marketplace", label: "Marketplace", icon: Store },
      { href: "/app/creator", label: "Creator Dashboard", icon: UserCog },
      { href: "/app/campaigns", label: "Missions", icon: Rocket },
      { href: "/app/leads", label: "Leads", icon: Users },
      { href: "/app/replies", label: "Interested Replies", icon: Sparkles },
      { href: "/app/meetings", label: "Meeting Pipeline", icon: BriefcaseBusiness }
    ]
  },
  {
    id: "platform",
    label: "Platform",
    items: [
      { href: "/app/integrations", label: "Integrations", icon: Layers3 },
      { href: "/app/settings/billing", label: "Billing", icon: BarChart3 },
      { href: "/app/admin", label: "Admin", icon: Shield },
      { href: "/app/settings", label: "Settings", icon: Settings }
    ]
  }
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({});

  const toggleGroup = (groupId: string) => {
    setCollapsedGroups((current) => ({ ...current, [groupId]: !current[groupId] }));
  };

  return (
    <aside className="hidden w-72 border-r border-slate-200/70 bg-slate-950/70 p-4 backdrop-blur-lg lg:block">
      <div className="mb-8 rounded-2xl border border-slate-200/40 bg-slate-900/60 p-4 shadow-2xl shadow-blue-950/25">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">Thorpe Workforce</p>
        <h2 className="mt-2 text-lg font-semibold text-slate-100">AI Operating System</h2>
        <p className="mt-2 text-xs text-slate-500">Digital workers, live runs, and autonomous momentum.</p>
      </div>
      <nav className="space-y-4">
        {navGroups.map((group) => {
          const isCollapsed = Boolean(collapsedGroups[group.id]);
          return (
            <div key={group.id} className="rounded-xl border border-slate-200/40 bg-slate-900/30 p-2">
              <button
                type="button"
                onClick={() => toggleGroup(group.id)}
                className="flex w-full items-center justify-between px-2 py-1 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 hover:text-cyan-300"
              >
                <span>{group.label}</span>
                {isCollapsed ? <ChevronRight className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
              </button>
              {!isCollapsed ? (
                <div className="mt-1 space-y-1">
                  {group.items.map((item) => {
                    const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
                    const Icon = item.icon;
                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        className={clsx(
                          "flex items-center gap-2 rounded-lg px-2.5 py-2 text-sm font-medium transition",
                          isActive
                            ? "bg-gradient-to-r from-blue-500/25 to-cyan-400/15 text-cyan-100 shadow-md shadow-cyan-900/30"
                            : "text-slate-400 hover:bg-slate-800/80 hover:text-slate-100"
                        )}
                      >
                        <Icon className={clsx("h-4 w-4", isActive ? "text-cyan-300" : "text-slate-500")} />
                        <span>{item.label}</span>
                      </Link>
                    );
                  })}
                </div>
              ) : null}
            </div>
          );
        })}
      </nav>
    </aside>
  );
}
