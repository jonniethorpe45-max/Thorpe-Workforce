"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { CampaignForm } from "@/components/forms/CampaignForm";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { api } from "@/services/api";

type WorkerOption = { id: string; name: string };

export default function NewCampaignPage() {
  const router = useRouter();
  const [workers, setWorkers] = useState<WorkerOption[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<WorkerOption[]>("/workers")
      .then(setWorkers)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load workers"));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!workers) return <LoadingState label="Loading worker options..." />;

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">New Campaign</h2>
      <CampaignForm
        workerOptions={workers}
        onSubmit={async (payload) => {
          try {
            const created = await api.post<{ id: string }>("/campaigns", payload);
            router.push(`/app/campaigns/${created.id}`);
          } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to create campaign");
          }
        }}
      />
    </div>
  );
}
