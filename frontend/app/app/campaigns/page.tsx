"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/services/api";
import type { Campaign } from "@/types";

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<Campaign[]>("/campaigns")
      .then(setCampaigns)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load campaigns"));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!campaigns) return <LoadingState label="Loading campaigns..." />;

  if (!campaigns.length) {
    return (
      <EmptyState
        title="No campaigns yet"
        description="Create your first worker mission and attach an AI Sales Worker."
        action={
          <Link href="/app/campaigns/new" className="btn-primary">
            Create Campaign
          </Link>
        }
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Missions</h2>
        <Link href="/app/campaigns/new" className="btn-primary">
          Create Mission
        </Link>
      </div>
      <div className="card overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-100 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3">Mission</th>
              <th className="px-4 py-3">Industry</th>
              <th className="px-4 py-3">Mission Status</th>
            </tr>
          </thead>
          <tbody>
            {campaigns.map((campaign) => (
              <tr key={campaign.id} className="border-t border-slate-200">
                <td className="px-4 py-3">
                  <Link href={`/app/campaigns/${campaign.id}`} className="font-medium text-brand-600 hover:underline">
                    {campaign.name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-600">{campaign.target_industry || "-"}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={campaign.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
