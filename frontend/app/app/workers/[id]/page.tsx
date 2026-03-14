"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/services/api";
import type { Worker } from "@/types";

export default function WorkerDetailPage() {
  const params = useParams<{ id: string }>();
  const [worker, setWorker] = useState<Worker | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<Worker>(`/workers/${params.id}`)
      .then(setWorker)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load worker"));
  }, [params.id]);

  if (error) return <ErrorState message={error} />;
  if (!worker) return <LoadingState label="Loading worker..." />;

  return (
    <div className="space-y-4">
      <div className="card p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold">{worker.name}</h2>
          <StatusBadge status={worker.status} />
        </div>
        <p className="mt-2 text-slate-600">{worker.goal}</p>
        <p className="mt-3 text-sm text-slate-500">Daily send limit: {worker.send_limit_per_day}</p>
      </div>
    </div>
  );
}
