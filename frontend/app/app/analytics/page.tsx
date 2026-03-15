"use client";

import { useEffect, useState } from "react";
import { Activity, BarChart3, Gauge, Layers3, Sparkles } from "lucide-react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { TableShell } from "@/components/tables/TableShell";
import { api } from "@/services/api";
import type { WorkspaceActivityRead, WorkspaceAnalyticsSummaryRead, WorkspaceUsageHistoryPointRead } from "@/types";

export default function WorkspaceAnalyticsPage() {
  const [summary, setSummary] = useState<WorkspaceAnalyticsSummaryRead | null>(null);
  const [activity, setActivity] = useState<WorkspaceActivityRead[]>([]);
  const [history, setHistory] = useState<WorkspaceUsageHistoryPointRead[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api.get<WorkspaceAnalyticsSummaryRead>("/analytics/workspace/summary?range=30d"),
      api.get<WorkspaceActivityRead[]>("/analytics/workspace/activity?limit=20"),
      api.get<WorkspaceUsageHistoryPointRead[]>("/analytics/workspace/usage-history?range=30d")
    ])
      .then(([summaryRes, activityRes, historyRes]) => {
        setSummary(summaryRes);
        setActivity(activityRes);
        setHistory(historyRes);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load workspace analytics"));
  }, []);

  if (error && !summary) return <ErrorState message={error} />;
  if (!summary) return <LoadingState label="Loading workspace analytics..." />;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="section-title">Workspace Analytics</h2>
        <p className="section-subtitle">Usage, limits, and recent activity across your AI workforce.</p>
      </div>

      {error ? <ErrorState message={error} /> : null}

      <div className="kpi-grid">
        <StatCard label="Total Runs" value={summary.total_runs} icon={<Activity className="h-4 w-4" />} />
        <StatCard label="Runs This Period" value={summary.runs_this_period} icon={<BarChart3 className="h-4 w-4" />} />
        <StatCard label="Success Rate" value={`${(summary.success_rate * 100).toFixed(1)}%`} icon={<Gauge className="h-4 w-4" />} />
      </div>

      <div className="card p-4">
        <h3 className="text-base font-semibold">Usage vs Plan Limits</h3>
        <div className="mt-2 grid gap-2 text-sm md:grid-cols-2">
          <p>
            Plan: <span className="chip">{summary.plan.name}</span>
          </p>
          <p>Installed Workers: {summary.usage.worker_installs} / {summary.limits.max_worker_installs_per_workspace ?? "∞"}</p>
          <p>Worker Runs (month): {summary.usage.worker_runs_month} / {summary.limits.max_worker_runs_per_month ?? "∞"}</p>
          <p>Published Workers: {summary.usage.published_workers} / {summary.limits.max_published_workers ?? "∞"}</p>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card p-4">
          <h3 className="inline-flex items-center gap-2 text-base font-semibold">
            <Layers3 className="h-4 w-4 text-cyan-300" />
            Top Used Workers
          </h3>
          <ul className="mt-2 space-y-2 text-sm">
            {summary.top_used_workers.length === 0 ? (
              <li>No usage yet.</li>
            ) : (
              summary.top_used_workers.map((item, idx) => (
                <li key={idx} className="rounded-lg border border-slate-200/70 bg-slate-900/40 px-3 py-2">
                  <span className="font-medium">{String(item.name)}</span> — {String(item.runs)} runs
                </li>
              ))
            )}
          </ul>
        </div>
        <div className="card p-4">
          <h3 className="inline-flex items-center gap-2 text-base font-semibold">
            <Sparkles className="h-4 w-4 text-indigo-300" />
            Recent Activity
          </h3>
          <ul className="mt-2 space-y-2 text-sm">
            {activity.length === 0 ? (
              <li>No recent activity.</li>
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

      <TableShell>
        <div className="border-b border-slate-200/60 px-4 py-3">
          <h3 className="text-base font-semibold">Usage History (30d)</h3>
        </div>
        <div className="p-4">
          <div className="max-h-72 overflow-auto">
            <table className="min-w-full text-sm">
              <thead className="text-left text-slate-500">
                <tr><th className="py-1">Date</th><th className="py-1">Runs</th><th className="py-1">Chain Runs</th><th className="py-1">Installs</th><th className="py-1">Failed</th></tr>
              </thead>
              <tbody>
                {history.map((point) => (
                  <tr key={point.date} className="border-t border-slate-100">
                    <td className="py-1 font-mono">{point.date}</td>
                    <td className="py-1">{point.worker_runs}</td>
                    <td className="py-1">{point.chain_runs}</td>
                    <td className="py-1">{point.installs}</td>
                    <td className="py-1">{point.failed_runs}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </TableShell>
    </div>
  );
}
