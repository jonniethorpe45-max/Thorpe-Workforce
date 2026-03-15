"use client";

import { useEffect, useState } from "react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
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
        <h2 className="text-2xl font-semibold">Workspace Analytics</h2>
        <p className="text-sm text-slate-600">Usage, limits, and recent activity across your AI workforce.</p>
      </div>

      {error ? <ErrorState message={error} /> : null}

      <div className="grid gap-3 md:grid-cols-3">
        <div className="card p-4"><p className="text-xs text-slate-500">Total Runs</p><p className="text-2xl font-semibold">{summary.total_runs}</p></div>
        <div className="card p-4"><p className="text-xs text-slate-500">Runs This Period</p><p className="text-2xl font-semibold">{summary.runs_this_period}</p></div>
        <div className="card p-4"><p className="text-xs text-slate-500">Success Rate</p><p className="text-2xl font-semibold">{(summary.success_rate * 100).toFixed(1)}%</p></div>
      </div>

      <div className="card p-4">
        <h3 className="text-base font-semibold">Usage vs Plan Limits</h3>
        <div className="mt-2 grid gap-2 text-sm md:grid-cols-2">
          <p>Plan: <span className="font-medium">{summary.plan.name}</span></p>
          <p>Installed Workers: {summary.usage.worker_installs} / {summary.limits.max_worker_installs_per_workspace ?? "∞"}</p>
          <p>Worker Runs (month): {summary.usage.worker_runs_month} / {summary.limits.max_worker_runs_per_month ?? "∞"}</p>
          <p>Published Workers: {summary.usage.published_workers} / {summary.limits.max_published_workers ?? "∞"}</p>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card p-4">
          <h3 className="text-base font-semibold">Top Used Workers</h3>
          <ul className="mt-2 space-y-2 text-sm">
            {summary.top_used_workers.length === 0 ? <li>No usage yet.</li> : summary.top_used_workers.map((item, idx) => <li key={idx}>{String(item.name)} — {String(item.runs)} runs</li>)}
          </ul>
        </div>
        <div className="card p-4">
          <h3 className="text-base font-semibold">Recent Activity</h3>
          <ul className="mt-2 space-y-2 text-sm">
            {activity.length === 0 ? <li>No recent activity.</li> : activity.map((item, idx) => <li key={idx}>{item.event_name} — {new Date(item.created_at).toLocaleString()}</li>)}
          </ul>
        </div>
      </div>

      <div className="card p-4">
        <h3 className="text-base font-semibold">Usage History (30d)</h3>
        <div className="mt-2 max-h-72 overflow-auto">
          <table className="min-w-full text-sm">
            <thead className="text-left text-slate-500">
              <tr><th className="py-1">Date</th><th className="py-1">Runs</th><th className="py-1">Chain Runs</th><th className="py-1">Installs</th><th className="py-1">Failed</th></tr>
            </thead>
            <tbody>
              {history.map((point) => (
                <tr key={point.date} className="border-t border-slate-100">
                  <td className="py-1">{point.date}</td>
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
    </div>
  );
}
