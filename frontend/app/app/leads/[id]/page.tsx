"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/services/api";
import type { Lead } from "@/types";

export default function LeadDetailPage() {
  const params = useParams<{ id: string }>();
  const [lead, setLead] = useState<Lead | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<Lead>(`/leads/${params.id}`)
      .then(setLead)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load lead"));
  }, [params.id]);

  if (error) return <ErrorState message={error} />;
  if (!lead) return <LoadingState label="Loading lead..." />;

  return (
    <div className="space-y-4">
      <div className="card p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold">{lead.full_name || lead.email}</h2>
          <StatusBadge status={lead.lead_status} />
        </div>
        <p className="mt-2 text-slate-600">{lead.title || "No title available"}</p>
        <p className="text-sm text-slate-500">{lead.company_name}</p>
        <p className="mt-2 text-sm text-slate-500">{lead.email}</p>
        <p className="text-sm text-slate-500">{lead.location || "Location unknown"}</p>
      </div>
    </div>
  );
}
