"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
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

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Worker Analytics</h2>
      {error ? <ErrorState message={error} /> : null}

      <div className="grid gap-4 md:grid-cols-2">
        <div className="card p-4">
          <h3 className="text-base font-semibold">Runs Trend</h3>
          <ul className="mt-2 max-h-64 space-y-1 overflow-auto text-sm">
            {analytics.runs_over_time.map((point) => (
              <li key={`run-${point.date}`} className="flex justify-between">
                <span>{point.date}</span>
                <span>{point.value}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="card p-4">
          <h3 className="text-base font-semibold">Installs Trend</h3>
          <ul className="mt-2 max-h-64 space-y-1 overflow-auto text-sm">
            {analytics.installs_over_time.map((point) => (
              <li key={`install-${point.date}`} className="flex justify-between">
                <span>{point.date}</span>
                <span>{point.value}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="card p-4">
        <h3 className="text-base font-semibold">Recent Failures</h3>
        <ul className="mt-2 space-y-2 text-sm">
          {analytics.recent_failures.length === 0 ? <li>No recent failures.</li> : analytics.recent_failures.map((item, idx) => <li key={idx}>{String(item.error_message ?? "Unknown error")} — {String(item.created_at ?? "")}</li>)}
        </ul>
      </div>
    </div>
  );
}
