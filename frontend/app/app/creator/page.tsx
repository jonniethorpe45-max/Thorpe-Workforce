"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
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
        <h2 className="text-2xl font-semibold">Creator Dashboard</h2>
        <p className="text-sm text-slate-600">Monitor installs, runs, monetization signals, and moderation status.</p>
      </div>
      {error ? <ErrorState message={error} /> : null}

      <div className="grid gap-3 md:grid-cols-4">
        <div className="card p-4"><p className="text-xs text-slate-500">Published Workers</p><p className="text-2xl font-semibold">{summary.published_workers_count}</p></div>
        <div className="card p-4"><p className="text-xs text-slate-500">Total Installs</p><p className="text-2xl font-semibold">{summary.total_installs}</p></div>
        <div className="card p-4"><p className="text-xs text-slate-500">Total Runs</p><p className="text-2xl font-semibold">{summary.total_runs}</p></div>
        <div className="card p-4"><p className="text-xs text-slate-500">Creator Revenue (est.)</p><p className="text-2xl font-semibold">${(payout.estimated_creator_share / 100).toFixed(2)}</p></div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card p-4">
          <h3 className="text-base font-semibold">Top Workers</h3>
          <ul className="mt-2 space-y-2 text-sm">
            {workers.slice(0, 8).map((worker) => (
              <li key={worker.worker_template_id} className="flex items-center justify-between gap-2">
                <div>
                  <p className="font-medium">{worker.name}</p>
                  <p className="text-xs text-slate-500">{worker.pricing_type} • moderation: {worker.moderation_status}</p>
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
          <h3 className="text-base font-semibold">Recent Activity</h3>
          <ul className="mt-2 space-y-2 text-sm">
            {activity.length === 0 ? <li>No recent creator activity.</li> : activity.map((item, idx) => <li key={idx}>{item.event_name} — {new Date(item.created_at).toLocaleString()}</li>)}
          </ul>
        </div>
      </div>
    </div>
  );
}
