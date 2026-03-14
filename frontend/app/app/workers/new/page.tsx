"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { WorkerForm } from "@/components/forms/WorkerForm";
import { ErrorState } from "@/components/ui/ErrorState";
import { api } from "@/services/api";

export default function NewWorkerPage() {
  const router = useRouter();
  const [error, setError] = useState("");

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Create AI Sales Worker</h2>
      {error ? <ErrorState message={error} /> : null}
      <WorkerForm
        onSubmit={async (payload) => {
          try {
            const created = await api.post<{ id: string }>("/workers", payload);
            router.push(`/app/workers/${created.id}`);
          } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to create worker");
          }
        }}
      />
    </div>
  );
}
