"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { TableShell } from "@/components/tables/TableShell";
import { api } from "@/services/api";
import type { Worker } from "@/types";

export default function WorkersPage() {
  const [workers, setWorkers] = useState<Worker[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<Worker[]>("/workers")
      .then(setWorkers)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load workers"));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!workers) return <LoadingState label="Loading workers..." />;

  if (!workers.length) {
    return (
      <EmptyState
        title="No workers yet"
        description="Create your first AI Sales Worker to launch a recurring mission."
        action={
          <Link href="/app/workers/new" className="btn-primary">
            Create Worker
          </Link>
        }
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="section-title">AI Sales Workers</h2>
        <Link href="/app/workers/new" className="btn-primary">
          Create Worker
        </Link>
      </div>
      <TableShell>
        <div className="border-b border-slate-200/60 px-4 py-3 text-sm text-slate-500">
          Worker registry · {workers.length} active definitions
        </div>
        <table className="min-w-full text-sm">
          <thead className="text-left text-slate-600">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Goal</th>
              <th className="px-4 py-3">Template</th>
              <th className="px-4 py-3">Worker Status</th>
              <th className="px-4 py-3">Daily Limit</th>
              <th className="px-4 py-3">Next Run</th>
            </tr>
          </thead>
          <tbody>
            {workers.map((worker) => (
              <tr key={worker.id} className="border-t border-slate-200">
                <td className="px-4 py-3">
                  <Link className="font-medium text-brand-600 hover:underline" href={`/app/workers/${worker.id}`}>
                    {worker.name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-600">{worker.goal}</td>
                <td className="px-4 py-3 text-slate-600">{worker.worker_type}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={worker.status} />
                </td>
                <td className="px-4 py-3">{worker.send_limit_per_day}</td>
                <td className="px-4 py-3 text-slate-600">
                  {worker.next_run_at ? new Date(worker.next_run_at).toLocaleString() : "Not scheduled"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableShell>
    </div>
  );
}
