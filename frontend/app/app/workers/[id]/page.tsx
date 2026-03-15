"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/services/api";
import type { Campaign, Worker, WorkerRun } from "@/types";

export default function WorkerDetailPage() {
  const params = useParams<{ id: string }>();
  const [worker, setWorker] = useState<Worker | null>(null);
  const [runs, setRuns] = useState<WorkerRun[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const [workerData, runsData, campaignData] = await Promise.all([
      api.get<Worker>(`/workers/${params.id}`),
      api.get<WorkerRun[]>(`/workers/${params.id}/runs`),
      api.get<Campaign[]>("/campaigns")
    ]);
    setWorker(workerData);
    setRuns(runsData);
    setCampaigns(campaignData.filter((campaign) => campaign.worker_id === params.id));
  }, [params.id]);

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load worker"));
  }, [load]);

  if (error) return <ErrorState message={error} />;
  if (!worker) return <LoadingState label="Loading worker..." />;

  const campaignForRun = campaigns[0];

  return (
    <div className="space-y-4">
      <div className="card p-6">
        <div className="flex items-center justify-between">
          <h2 className="section-title">{worker.name}</h2>
          <StatusBadge status={worker.status} />
        </div>
        <p className="mt-2 text-slate-600">Mission: {worker.mission || worker.goal}</p>
        <p className="text-sm text-slate-500">
          Definition: {worker.worker_type} • Plan {worker.plan_version}
        </p>
        <p className="mt-3 text-sm text-slate-500">Daily send limit: {worker.send_limit_per_day}</p>
        <p className="text-sm text-slate-500">Run cadence: every {worker.run_interval_minutes} minutes</p>
        <p className="text-sm text-slate-500">
          Current task window: {worker.next_run_at ? new Date(worker.next_run_at).toLocaleString() : "Not scheduled"}
        </p>
        {worker.last_error_text ? (
          <p className="mt-2 rounded-md border border-rose-300/40 bg-rose-950/20 px-3 py-2 text-sm text-rose-200">{worker.last_error_text}</p>
        ) : null}
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            className="btn-secondary"
            disabled={busy || worker.status === "paused"}
            onClick={async () => {
              setBusy(true);
              try {
                await api.post(`/workers/${worker.id}/pause`, {});
                await load();
              } finally {
                setBusy(false);
              }
            }}
          >
            Pause Worker
          </button>
          <button
            className="btn-secondary"
            disabled={busy || worker.status !== "paused"}
            onClick={async () => {
              setBusy(true);
              try {
                await api.post(`/workers/${worker.id}/resume`, {});
                await load();
              } finally {
                setBusy(false);
              }
            }}
          >
            Resume Worker
          </button>
          <button
            className="btn-primary"
            disabled={busy || !campaignForRun}
            onClick={async () => {
              if (!campaignForRun) return;
              setBusy(true);
              try {
                await api.post(`/workers/${worker.id}/execute?campaign_id=${campaignForRun.id}`, {});
                await load();
              } finally {
                setBusy(false);
              }
            }}
          >
            Run Worker Now
          </button>
        </div>
      </div>
      <div className="card p-4">
        <h3 className="text-base font-semibold">Recent Runs</h3>
        <div className="mt-3 space-y-2">
          {runs.length === 0 ? (
            <p className="text-sm text-slate-600">No runs yet. Launch a campaign mission to start execution.</p>
          ) : (
            runs.map((run) => (
              <div key={run.id} className="rounded-md border border-slate-200 p-3">
                <div className="flex items-center justify-between">
                  <p className="font-medium">{run.run_type}</p>
                  <StatusBadge status={run.status} />
                </div>
                <p className="font-mono text-xs text-slate-500">Started {new Date(run.started_at).toLocaleString()}</p>
                {run.finished_at ? (
                  <p className="font-mono text-xs text-slate-500">Finished {new Date(run.finished_at).toLocaleString()}</p>
                ) : null}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
