"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Activity, AlertTriangle, ChartNoAxesCombined, Download, Rocket } from "lucide-react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { api } from "@/services/api";
import type { CreatorWorkerAnalyticsRead } from "@/types";

export default function CreatorWorkerAnalyticsPage() {
  const params = useParams<{ id: string }>();
  const [analytics, setAnalytics] = useState<CreatorWorkerAnalyticsRead | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<CreatorWorkerAnalyticsRead>(`/creator/workers/${params.id}/analytics?range=30d`)
      .then(setAnalytics)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load worker analytics"));
  }, [params.id]);

  if (error && !analytics) return <ErrorState message={error} />;
  if (!analytics) return <LoadingState label="Loading worker analytics..." />;

  const totalRuns = analytics.runs_over_time.reduce((sum, point) => sum + point.value, 0);
  const totalInstalls = analytics.installs_over_time.reduce((sum, point) => sum + point.value, 0);

  return (
    <div className="space-y-4">
      <h2 className="section-title">Worker Analytics</h2>
      {error ? <ErrorState message={error} /> : null}

      <div className="kpi-grid">
        <StatCard label="Runs in range" value={totalRuns} icon={<Activity className="h-4 w-4" />} />
        <StatCard label="Installs in range" value={totalInstalls} icon={<Rocket className="h-4 w-4" />} />
        <StatCard label="Recent failures" value={analytics.recent_failures.length} icon={<AlertTriangle className="h-4 w-4" />} />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="card p-4">
          <h3 className="inline-flex items-center gap-2 text-base font-semibold">
            <ChartNoAxesCombined className="h-4 w-4 text-cyan-300" />
            Runs Trend
          </h3>
          <ul className="mt-2 max-h-64 space-y-1 overflow-auto text-sm">
            {analytics.runs_over_time.map((point) => (
              <li key={`run-${point.date}`} className="flex justify-between rounded-md border border-slate-200/60 bg-slate-900/35 px-2 py-1.5">
                <span className="font-mono">{point.date}</span>
                <span>{point.value}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="card p-4">
          <h3 className="inline-flex items-center gap-2 text-base font-semibold">
            <Download className="h-4 w-4 text-indigo-300" />
            Installs Trend
          </h3>
          <ul className="mt-2 max-h-64 space-y-1 overflow-auto text-sm">
            {analytics.installs_over_time.map((point) => (
              <li key={`install-${point.date}`} className="flex justify-between rounded-md border border-slate-200/60 bg-slate-900/35 px-2 py-1.5">
                <span className="font-mono">{point.date}</span>
                <span>{point.value}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="card p-4">
        <h3 className="text-base font-semibold">Recent Failures</h3>
        <ul className="mt-2 space-y-2 text-sm">
          {analytics.recent_failures.length === 0 ? (
            <li>No recent failures.</li>
          ) : (
            analytics.recent_failures.map((item, idx) => (
              <li key={idx} className="rounded-md border border-rose-300/35 bg-rose-950/20 px-3 py-2">
                <p className="text-rose-200">{String(item.error_message ?? "Unknown error")}</p>
                <p className="mt-1 text-xs text-rose-300/80">{String(item.created_at ?? "")}</p>
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );
}
