"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { BarChart3 } from "lucide-react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { TableShell } from "@/components/tables/TableShell";
import { api } from "@/services/api";
import type { CreatorWorkerSummaryRead } from "@/types";

export default function CreatorWorkersPage() {
  const [workers, setWorkers] = useState<CreatorWorkerSummaryRead[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<CreatorWorkerSummaryRead[]>("/creator/workers")
      .then(setWorkers)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load creator workers"));
  }, []);

  if (error && !workers) return <ErrorState message={error} />;
  if (!workers) return <LoadingState label="Loading creator workers..." />;

  return (
    <div className="space-y-4">
      <h2 className="section-title">Creator Workers</h2>
      {error ? <ErrorState message={error} /> : null}
      <TableShell>
        <div className="flex items-center justify-between border-b border-slate-200/60 px-4 py-3">
          <p className="inline-flex items-center gap-2 text-sm font-semibold text-slate-700">
            <BarChart3 className="h-4 w-4 text-cyan-300" />
            Worker performance table
          </p>
          <span className="text-xs text-slate-500">{workers.length} templates</span>
        </div>
        <div className="p-4">
        <table className="min-w-full text-sm">
          <thead className="text-left text-slate-500">
            <tr>
              <th className="py-2">Worker</th>
              <th className="py-2">Pricing</th>
              <th className="py-2">Installs</th>
              <th className="py-2">Runs</th>
              <th className="py-2">Revenue (est.)</th>
              <th className="py-2">Moderation</th>
              <th className="py-2" />
            </tr>
          </thead>
          <tbody>
            {workers.map((worker) => (
              <tr key={worker.worker_template_id} className="border-t border-slate-100">
                <td className="py-2">{worker.name}</td>
                <td className="py-2"><span className="chip">{worker.pricing_type}</span></td>
                <td className="py-2">{worker.installs}</td>
                <td className="py-2">{worker.runs}</td>
                <td className="py-2">${(worker.estimated_revenue / 100).toFixed(2)}</td>
                <td className="py-2"><StatusBadge status={worker.moderation_status} /></td>
                <td className="py-2">
                  <Link className="text-brand-600 hover:underline" href={`/app/creator/workers/${worker.worker_template_id}`}>
                    Analytics
                  </Link>
                </td>
              </tr>
            ))}
            {!workers.length ? (
              <tr>
                <td className="py-4 text-slate-500" colSpan={7}>
                  No worker analytics available yet.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
        </div>
      </TableShell>
    </div>
  );
}
