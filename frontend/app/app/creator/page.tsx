"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Activity, DollarSign, Layers3, Rocket, Sparkles } from "lucide-react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { api } from "@/services/api";
import type { CreatorActivityItemRead, CreatorDashboardSummaryRead, CreatorPayoutsSummaryRead, CreatorWorkerSummaryRead } from "@/types";

export default function CreatorDashboardPage() {
  const [summary, setSummary] = useState<CreatorDashboardSummaryRead | null>(null);
  const [workers, setWorkers] = useState<CreatorWorkerSummaryRead[]>([]);
  const [activity, setActivity] = useState<CreatorActivityItemRead[]>([]);
  const [payout, setPayout] = useState<CreatorPayoutsSummaryRead | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api.get<CreatorDashboardSummaryRead>("/creator/dashboard/summary?range=30d"),
      api.get<CreatorWorkerSummaryRead[]>("/creator/workers"),
      api.get<CreatorActivityItemRead[]>("/creator/activity?limit=20"),
      api.get<CreatorPayoutsSummaryRead>("/creator/payouts/summary?range=30d")
    ])
      .then(([summaryRes, workersRes, activityRes, payoutRes]) => {
        setSummary(summaryRes);
        setWorkers(workersRes);
        setActivity(activityRes);
        setPayout(payoutRes);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load creator dashboard"));
  }, []);

  if (error && !summary) return <ErrorState message={error} />;
  if (!summary || !payout) return <LoadingState label="Loading creator dashboard..." />;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="section-title">Creator Dashboard</h2>
        <p className="section-subtitle">Monitor installs, runs, monetization signals, and moderation status.</p>
      </div>
      {error ? <ErrorState message={error} /> : null}

      <div className="kpi-grid">
        <StatCard label="Published Workers" value={summary.published_workers_count} icon={<Layers3 className="h-4 w-4" />} />
        <StatCard label="Total Installs" value={summary.total_installs} icon={<Rocket className="h-4 w-4" />} />
        <StatCard label="Total Runs" value={summary.total_runs} icon={<Activity className="h-4 w-4" />} />
        <StatCard label="Creator Revenue (est.)" value={`$${(payout.estimated_creator_share / 100).toFixed(2)}`} icon={<DollarSign className="h-4 w-4" />} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card p-4">
          <h3 className="inline-flex items-center gap-2 text-base font-semibold">
            <Sparkles className="h-4 w-4 text-cyan-300" />
            Top Workers
          </h3>
          <ul className="mt-2 space-y-2 text-sm">
            {workers.slice(0, 8).map((worker) => (
              <li key={worker.worker_template_id} className="flex items-center justify-between gap-2 rounded-lg border border-slate-200/70 bg-slate-900/40 px-3 py-2">
                <div>
                  <p className="font-medium">{worker.name}</p>
                  <p className="text-xs text-slate-500">
                    <span className="chip mr-1.5">{worker.pricing_type}</span>
                    moderation: {worker.moderation_status}
                  </p>
                </div>
                <Link className="text-xs text-brand-600 hover:underline" href={`/app/creator/workers/${worker.worker_template_id}`}>
                  View
                </Link>
              </li>
            ))}
            {!workers.length ? <li>No creator workers yet.</li> : null}
          </ul>
          <div className="mt-3">
            <Link className="text-sm text-brand-600 hover:underline" href="/app/creator/workers">
              View all workers →
            </Link>
          </div>
        </div>

        <div className="card p-4">
          <h3 className="inline-flex items-center gap-2 text-base font-semibold">
            <Activity className="h-4 w-4 text-indigo-300" />
            Recent Activity
          </h3>
          <ul className="mt-2 space-y-2 text-sm">
            {activity.length === 0 ? (
              <li>No recent creator activity.</li>
            ) : (
              activity.map((item, idx) => (
                <li key={idx} className="rounded-lg border border-slate-200/70 bg-slate-900/40 px-3 py-2">
                  <p className="font-medium text-slate-700">{item.event_name}</p>
                  <p className="text-xs text-slate-500">{new Date(item.created_at).toLocaleString()}</p>
                </li>
              ))
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}
