"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { TableShell } from "@/components/tables/TableShell";
import { api } from "@/services/api";
import type { WorkerInstanceExecuteResponse, WorkerInstanceRead, WorkerTemplateRead } from "@/types";

function formatDate(value?: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

export default function WorkerInstancesPage() {
  const [instances, setInstances] = useState<WorkerInstanceRead[] | null>(null);
  const [templates, setTemplates] = useState<WorkerTemplateRead[]>([]);
  const [busyInstanceId, setBusyInstanceId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const templateById = useMemo(() => new Map(templates.map((item) => [item.id, item])), [templates]);

  const load = useCallback(async () => {
    setError("");
    const [instanceData, templateData] = await Promise.all([
      api.get<WorkerInstanceRead[]>("/workers/instances"),
      api.get<WorkerTemplateRead[]>("/workers/templates?include_public=true")
    ]);
    setInstances(instanceData);
    setTemplates(templateData);
  }, []);

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load worker instances"));
  }, [load]);

  const runNow = async (instanceId: string) => {
    try {
      setBusyInstanceId(instanceId);
      setError("");
      const response = await api.post<WorkerInstanceExecuteResponse>(`/workers/instances/${instanceId}/run`, {
        runtime_input: {},
        trigger_source: "instances_ui"
      });
      setMessage(
        response.queued
          ? `Run queued for instance ${instanceId.slice(0, 8)}…`
          : `Run executed immediately with status ${response.status}.`
      );
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run worker instance");
    } finally {
      setBusyInstanceId(null);
    }
  };

  const setInstanceStatus = async (instanceId: string, action: "pause" | "resume") => {
    try {
      setBusyInstanceId(instanceId);
      setError("");
      await api.post(`/workers/instances/${instanceId}/${action}`, {});
      setMessage(`Instance ${action}d.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${action} instance`);
    } finally {
      setBusyInstanceId(null);
    }
  };

  if (error && !instances) return <ErrorState message={error} />;
  if (!instances) return <LoadingState label="Loading worker instances..." />;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="section-title">Worker Instances</h2>
        <p className="text-sm text-slate-600">Manage installed workers, run on demand, and monitor run cadence.</p>
      </div>
      {error ? <ErrorState message={error} /> : null}
      {message ? <div className="card border-emerald-200/50 bg-emerald-950/20 p-3 text-sm text-emerald-200">{message}</div> : null}

      {!instances.length ? (
        <EmptyState
          title="No worker instances"
          description="Install a template from Worker Builder or Marketplace to create your first worker instance."
        />
      ) : (
        <TableShell>
          <div className="border-b border-slate-200/60 px-4 py-3 text-sm text-slate-500">Installed instances</div>
          <table className="min-w-full text-sm">
            <thead className="text-left text-slate-600">
              <tr>
                <th className="px-4 py-3">Instance</th>
                <th className="px-4 py-3">Template</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Memory</th>
                <th className="px-4 py-3">Last Run</th>
                <th className="px-4 py-3">Next Run</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {instances.map((instance) => {
                const template = templateById.get(instance.template_id);
                const isBusy = busyInstanceId === instance.id;
                return (
                  <tr key={instance.id} className="border-t border-slate-200">
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-900">{instance.name}</p>
                      <p className="text-xs text-slate-500">{instance.id.slice(0, 12)}…</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-slate-700">{template?.display_name || "Unknown template"}</p>
                      <p className="text-xs text-slate-500">{template?.worker_type || instance.template_id}</p>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={instance.status} />
                    </td>
                    <td className="px-4 py-3 text-slate-600">{instance.memory_scope}</td>
                    <td className="px-4 py-3 text-slate-600">{formatDate(instance.last_run_at)}</td>
                    <td className="px-4 py-3 text-slate-600">{formatDate(instance.next_run_at)}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <button className="btn-secondary px-3 py-1 text-xs" disabled={isBusy} onClick={() => runNow(instance.id)}>
                          Run now
                        </button>
                        {instance.status === "paused" ? (
                          <button
                            className="btn-secondary px-3 py-1 text-xs"
                            disabled={isBusy}
                            onClick={() => setInstanceStatus(instance.id, "resume")}
                          >
                            Resume
                          </button>
                        ) : (
                          <button
                            className="btn-secondary px-3 py-1 text-xs"
                            disabled={isBusy}
                            onClick={() => setInstanceStatus(instance.id, "pause")}
                          >
                            Pause
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </TableShell>
      )}
    </div>
  );
}
