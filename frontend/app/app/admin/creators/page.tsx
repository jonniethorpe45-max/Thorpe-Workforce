"use client";

import { useEffect, useState } from "react";
import { Users } from "lucide-react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { TableShell } from "@/components/tables/TableShell";
import { api } from "@/services/api";
import type { AdminCreatorListItemRead } from "@/types";

export default function AdminCreatorsPage() {
  const [creators, setCreators] = useState<AdminCreatorListItemRead[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<AdminCreatorListItemRead[]>("/admin/creators")
      .then(setCreators)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load creators"));
  }, []);

  if (error && !creators) return <ErrorState message={error} />;
  if (!creators) return <LoadingState label="Loading creators..." />;

  return (
    <div className="space-y-4">
      <h2 className="section-title">Admin Creators</h2>
      {error ? <ErrorState message={error} /> : null}
      <TableShell>
        <div className="flex items-center justify-between border-b border-slate-200/60 px-4 py-3">
          <p className="inline-flex items-center gap-2 text-sm font-semibold text-slate-700">
            <Users className="h-4 w-4 text-cyan-300" />
            Creator performance
          </p>
          <span className="text-xs text-slate-500">{creators.length} creators</span>
        </div>
        <div className="p-4">
        <table className="min-w-full text-sm">
          <thead className="text-left text-slate-500">
            <tr>
              <th className="py-2">Creator</th>
              <th className="py-2">Workers</th>
              <th className="py-2">Installs</th>
              <th className="py-2">Runs</th>
              <th className="py-2">Revenue (est.)</th>
              <th className="py-2">Moderation Issues</th>
            </tr>
          </thead>
          <tbody>
            {creators.map((creator) => (
              <tr key={creator.creator_user_id} className="border-t border-slate-100">
                <td className="py-2">{creator.full_name} <span className="text-xs text-slate-500">({creator.email})</span></td>
                <td className="py-2">{creator.published_workers}</td>
                <td className="py-2">{creator.installs}</td>
                <td className="py-2">{creator.runs}</td>
                <td className="py-2">${(creator.estimated_revenue / 100).toFixed(2)}</td>
                <td className="py-2">{creator.moderation_issues_count}</td>
              </tr>
            ))}
            {!creators.length ? <tr><td colSpan={6} className="py-4 text-slate-500">No creators found.</td></tr> : null}
          </tbody>
        </table>
        </div>
      </TableShell>
    </div>
  );
}
