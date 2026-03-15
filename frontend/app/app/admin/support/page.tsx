"use client";

import { useCallback, useEffect, useState } from "react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { api } from "@/services/api";
import type { SupportRequestRead } from "@/types";

export default function AdminSupportPage() {
  const [requests, setRequests] = useState<SupportRequestRead[] | null>(null);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError("");
    const res = await api.get<SupportRequestRead[]>("/support/requests");
    setRequests(res);
  }, []);

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load support requests"));
  }, [load]);

  const updateStatus = async (id: string, status: SupportRequestRead["status"]) => {
    try {
      setBusyId(id);
      await api.patch<SupportRequestRead>(`/support/requests/${id}`, { status });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update request");
    } finally {
      setBusyId(null);
    }
  };

  if (error && !requests) return <ErrorState message={error} />;
  if (!requests) return <LoadingState label="Loading support requests..." />;

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Support Requests</h2>
      {error ? <ErrorState message={error} /> : null}
      <div className="card p-4">
        <table className="min-w-full text-sm">
          <thead className="text-left text-slate-500">
            <tr>
              <th className="py-2">Created</th>
              <th className="py-2">Contact</th>
              <th className="py-2">Subject</th>
              <th className="py-2">Status</th>
              <th className="py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {requests.map((item) => (
              <tr key={item.id} className="border-t border-slate-100">
                <td className="py-2">{new Date(item.created_at).toLocaleString()}</td>
                <td className="py-2">
                  <p className="font-medium">{item.name}</p>
                  <p className="text-xs text-slate-500">{item.email}</p>
                </td>
                <td className="py-2">
                  <p className="font-medium">{item.subject}</p>
                  <p className="text-xs text-slate-500">{item.message.slice(0, 120)}{item.message.length > 120 ? "…" : ""}</p>
                </td>
                <td className="py-2">{item.status}</td>
                <td className="py-2">
                  <div className="flex gap-2">
                    <button className="btn-secondary px-2 py-1 text-xs" disabled={busyId === item.id} onClick={() => updateStatus(item.id, "in_progress")}>
                      In Progress
                    </button>
                    <button className="btn-secondary px-2 py-1 text-xs" disabled={busyId === item.id} onClick={() => updateStatus(item.id, "resolved")}>
                      Resolve
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {!requests.length ? (
              <tr><td className="py-4 text-slate-500" colSpan={5}>No support requests yet.</td></tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
