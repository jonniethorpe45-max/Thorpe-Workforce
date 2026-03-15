"use client";

import { useCallback, useEffect, useState } from "react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { api } from "@/services/api";
import type { AdminWorkerListItemRead } from "@/types";

export default function AdminWorkersPage() {
  const [workers, setWorkers] = useState<AdminWorkerListItemRead[] | null>(null);
  const [error, setError] = useState("");
  const [busyWorkerId, setBusyWorkerId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError("");
    const res = await api.get<AdminWorkerListItemRead[]>("/admin/workers");
    setWorkers(res);
  }, []);

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load admin workers"));
  }, [load]);

  const moderate = async (workerTemplateId: string, action: string) => {
    try {
      setBusyWorkerId(workerTemplateId);
      await api.post(`/admin/workers/${workerTemplateId}/moderate`, { action, moderation_notes: `Applied via admin UI: ${action}` });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to moderate worker");
    } finally {
      setBusyWorkerId(null);
    }
  };

  if (error && !workers) return <ErrorState message={error} />;
  if (!workers) return <LoadingState label="Loading admin workers..." />;

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Admin Workers</h2>
      {error ? <ErrorState message={error} /> : null}
      <div className="card p-4">
        <table className="min-w-full text-sm">
          <thead className="text-left text-slate-500">
            <tr>
              <th className="py-2">Worker</th>
              <th className="py-2">Pricing</th>
              <th className="py-2">Visibility</th>
              <th className="py-2">Moderation</th>
              <th className="py-2">Featured</th>
              <th className="py-2">Reports</th>
              <th className="py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {workers.map((worker) => (
              <tr key={worker.worker_template_id} className="border-t border-slate-100">
                <td className="py-2">{worker.name}</td>
                <td className="py-2">{worker.pricing_type}</td>
                <td className="py-2">{worker.visibility}</td>
                <td className="py-2">{worker.moderation_status}</td>
                <td className="py-2">{worker.is_featured ? `Yes (#${worker.featured_rank})` : "No"}</td>
                <td className="py-2">{worker.report_count}</td>
                <td className="py-2">
                  <div className="flex gap-2">
                    <button className="btn-secondary px-2 py-1 text-xs" disabled={busyWorkerId === worker.worker_template_id} onClick={() => moderate(worker.worker_template_id, "approve")}>Approve</button>
                    <button className="btn-secondary px-2 py-1 text-xs" disabled={busyWorkerId === worker.worker_template_id} onClick={() => moderate(worker.worker_template_id, "hide")}>Hide</button>
                    <button className="btn-secondary px-2 py-1 text-xs" disabled={busyWorkerId === worker.worker_template_id} onClick={() => moderate(worker.worker_template_id, "reject")}>Reject</button>
                    <button
                      className="btn-secondary px-2 py-1 text-xs"
                      disabled={busyWorkerId === worker.worker_template_id}
                      onClick={async () => {
                        try {
                          setBusyWorkerId(worker.worker_template_id);
                          await api.post(`/admin/workers/${worker.worker_template_id}/feature`, {
                            is_featured: !worker.is_featured,
                            featured_rank: worker.is_featured ? 0 : 10
                          });
                          await load();
                        } catch (err) {
                          setError(err instanceof Error ? err.message : "Failed to update feature flag");
                        } finally {
                          setBusyWorkerId(null);
                        }
                      }}
                    >
                      {worker.is_featured ? "Unfeature" : "Feature"}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {!workers.length ? (
              <tr><td colSpan={7} className="py-4 text-slate-500">No workers found.</td></tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
