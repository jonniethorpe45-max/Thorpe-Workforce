"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { DollarSign, ShieldCheck, Store, Users } from "lucide-react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { api } from "@/services/api";
import type { AdminAnalyticsSummaryRead } from "@/types";

export default function AdminDashboardPage() {
  const [summary, setSummary] = useState<AdminAnalyticsSummaryRead | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<AdminAnalyticsSummaryRead>("/admin/analytics/summary")
      .then(setSummary)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load admin summary"));
  }, []);

  if (error && !summary) return <ErrorState message={error} />;
  if (!summary) return <LoadingState label="Loading admin dashboard..." />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="section-title">Admin Dashboard</h2>
        <div className="flex gap-2">
          <Link className="btn-secondary" href="/app/admin/workers">Workers</Link>
          <Link className="btn-secondary" href="/app/admin/creators">Creators</Link>
          <Link className="btn-secondary" href="/app/admin/billing">Billing</Link>
          <Link className="btn-secondary" href="/app/admin/support">Support</Link>
        </div>
      </div>
      {error ? <ErrorState message={error} /> : null}
      <div className="kpi-grid">
        <StatCard label="Users" value={summary.total_users} icon={<Users className="h-4 w-4" />} />
        <StatCard label="Workspaces" value={summary.total_workspaces} icon={<ShieldCheck className="h-4 w-4" />} />
        <StatCard label="Published Workers" value={summary.total_published_workers} icon={<Store className="h-4 w-4" />} />
        <StatCard label="MRR (est.)" value={`$${(summary.estimated_mrr / 100).toFixed(2)}`} icon={<DollarSign className="h-4 w-4" />} />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card p-4">
          <h3 className="text-base font-semibold">Top Workers</h3>
          <ul className="mt-2 space-y-2 text-sm">
            {summary.top_workers.map((item, idx) => (
              <li key={idx} className="rounded-lg border border-slate-200/70 bg-slate-900/40 px-3 py-2">
                <span className="font-medium">{String(item.name)}</span> — {String(item.runs)} runs
              </li>
            ))}
          </ul>
        </div>
        <div className="card p-4">
          <h3 className="text-base font-semibold">Top Creators</h3>
          <ul className="mt-2 space-y-2 text-sm">
            {summary.top_creators.map((item, idx) => (
              <li key={idx} className="rounded-lg border border-slate-200/70 bg-slate-900/40 px-3 py-2">
                <span className="font-medium">{String(item.name)}</span> — ${((Number(item.estimated_revenue) || 0) / 100).toFixed(2)}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
