"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/services/api";
import type { Lead } from "@/types";

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<Lead[]>("/leads")
      .then(setLeads)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load leads"));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!leads) return <LoadingState label="Loading leads..." />;

  if (!leads.length) {
    return (
      <EmptyState title="No leads yet" description="Import leads via API or run your first campaign launch." />
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Leads</h2>
      <div className="card overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-100 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3">Lead</th>
              <th className="px-4 py-3">Company</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((lead) => (
              <tr key={lead.id} className="border-t border-slate-200">
                <td className="px-4 py-3">
                  <Link href={`/app/leads/${lead.id}`} className="font-medium text-brand-600 hover:underline">
                    {lead.full_name || lead.email}
                  </Link>
                </td>
                <td className="px-4 py-3">{lead.company_name}</td>
                <td className="px-4 py-3">{lead.email}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={lead.lead_status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
