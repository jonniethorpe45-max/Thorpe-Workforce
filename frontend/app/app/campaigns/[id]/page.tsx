"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/services/api";
import type { Campaign } from "@/types";

type Message = {
  id: string;
  subject_line: string;
  body_text: string;
  approval_status: string;
};

export default function CampaignDetailPage() {
  const params = useParams<{ id: string }>();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      const [campaignData, messageData] = await Promise.all([
        api.get<Campaign>(`/campaigns/${params.id}`),
        api.get<Message[]>(`/campaigns/${params.id}/messages`)
      ]);
      setCampaign(campaignData);
      setMessages(messageData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load campaign");
    }
  };

  useEffect(() => {
    load();
  }, [params.id]);

  if (error) return <ErrorState message={error} />;
  if (!campaign) return <LoadingState label="Loading campaign..." />;

  return (
    <div className="space-y-4">
      <div className="card p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold">{campaign.name}</h2>
          <StatusBadge status={campaign.status} />
        </div>
        <p className="mt-2 text-sm text-slate-600">Industry: {campaign.target_industry || "Any"}</p>
        <div className="mt-4 flex gap-3">
          <button
            className="btn-primary"
            onClick={async () => {
              await api.post(`/campaigns/${params.id}/launch`, {});
              await load();
            }}
          >
            Launch Campaign
          </button>
          <button
            className="btn-secondary"
            onClick={async () => {
              await api.post(`/campaigns/${params.id}/pause`, {});
              await load();
            }}
          >
            Pause Campaign
          </button>
        </div>
      </div>
      <div className="card p-4">
        <h3 className="text-base font-semibold">Generated Messages</h3>
        <div className="mt-3 space-y-3">
          {messages.length === 0 ? (
            <p className="text-sm text-slate-600">No messages generated yet. Launch the campaign to draft outreach.</p>
          ) : (
            messages.map((message) => (
              <div key={message.id} className="rounded-lg border border-slate-200 p-3">
                <div className="flex items-center justify-between">
                  <p className="font-medium">{message.subject_line}</p>
                  <StatusBadge status={message.approval_status} />
                </div>
                <p className="mt-1 whitespace-pre-line text-sm text-slate-600">{message.body_text}</p>
                <div className="mt-2 flex gap-2">
                  <button className="btn-secondary" onClick={() => api.post(`/messages/${message.id}/approve`, {})}>
                    Approve
                  </button>
                  <button className="btn-secondary" onClick={() => api.post(`/messages/${message.id}/reject`, {})}>
                    Reject
                  </button>
                  <button className="btn-secondary" onClick={() => api.post(`/messages/${message.id}/regenerate`, {})}>
                    Regenerate
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
