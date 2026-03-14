"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { TableShell } from "@/components/tables/TableShell";
import { api } from "@/services/api";
import type { PlatformWorkerRunRead, WorkerRunListResponse } from "@/types";

function formatDuration(durationMs?: number | null): string {
  if (!durationMs || durationMs < 0) return "—";
  if (durationMs < 1000) return `${durationMs} ms`;
  return `${(durationMs / 1000).toFixed(1)} s`;
}

export default function WorkerRunsPage() {
  const [runs, setRuns] = useState<PlatformWorkerRunRead[] | null>(null);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [error, setError] = useState("");

  const load = useCallback(async (status: string) => {
    setError("");
    const query = new URLSearchParams({ limit: "100" });
    if (status !== "all") {
      query.set("status", status);
    }
    const response = await api.get<WorkerRunListResponse>(`/worker-runs?${query.toString()}`);
    setRuns(response.items);
    setTotal(response.total);
  }, []);

  useEffect(() => {
    load(statusFilter).catch((err) => setError(err instanceof Error ? err.message : "Failed to load worker runs"));
  }, [load, statusFilter]);

  const statusOptions = useMemo(() => ["all", "queued", "running", "completed", "failed", "paused"], []);

  if (error && !runs) return <ErrorState message={error} />;
  if (!runs) return <LoadingState label="Loading worker runs..." />;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-2xl font-semibold">Worker Runs</h2>
          <p className="text-sm text-slate-600">Review execution history, summaries, and failures across worker instances.</p>
        </div>
        <label className="text-sm">
          <span className="mr-2 text-slate-600">Status</span>
          <select
            className="rounded-lg border border-slate-200 px-3 py-2"
            onChange={(event) => setStatusFilter(event.target.value)}
            value={statusFilter}
          >
            {statusOptions.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </label>
      </div>
      {error ? <ErrorState message={error} /> : null}
      {!runs.length ? (
        <EmptyState title="No worker runs yet" description="Trigger a worker instance run to populate execution history." />
      ) : (
        <TableShell>
          <table className="min-w-full text-sm">
            <thead className="bg-slate-100 text-left text-slate-600">
              <tr>
                <th className="px-4 py-3">Started</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Trigger</th>
                <th className="px-4 py-3">Duration</th>
                <th className="px-4 py-3">Summary</th>
                <th className="px-4 py-3">Error</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.id} className="border-t border-slate-200 align-top">
                  <td className="px-4 py-3 text-slate-700">
                    <p>{new Date(run.started_at).toLocaleString()}</p>
                    <p className="text-xs text-slate-500">{run.id.slice(0, 12)}…</p>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={run.status} />
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {run.triggered_by}
                    {run.trigger_source ? <p className="text-xs text-slate-500">{run.trigger_source}</p> : null}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{formatDuration(run.duration_ms)}</td>
                  <td className="max-w-md px-4 py-3 text-slate-700">{run.summary || "—"}</td>
                  <td className="max-w-md px-4 py-3 text-rose-700">{run.error_message || run.error_text || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="border-t border-slate-200 px-4 py-2 text-xs text-slate-500">Showing {runs.length} of {total} runs</div>
        </TableShell>
      )}
    </div>
  );
}
