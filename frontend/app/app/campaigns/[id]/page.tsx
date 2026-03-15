"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

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
  const [actionMessage, setActionMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
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
  }, [params.id]);

  useEffect(() => {
    load();
  }, [load]);

  if (error) return <ErrorState message={error} />;
  if (!campaign) return <LoadingState label="Loading campaign..." />;
  const pending = messages.filter((m) => m.approval_status === "pending").length;
  const approved = messages.filter((m) => m.approval_status === "approved").length;

  return (
    <div className="space-y-4">
      <div className="card p-6">
        <div className="flex items-center justify-between">
          <h2 className="section-title">{campaign.name}</h2>
          <StatusBadge status={campaign.status} />
        </div>
        <p className="mt-2 text-sm text-slate-600">Mission focus: {campaign.target_industry || "Any industry"}</p>
        <p className="mt-1 text-sm text-slate-500">Approval queue: {pending} pending • {approved} approved</p>
        {actionMessage ? (
          <p className="mt-3 rounded-md border border-emerald-300/40 bg-emerald-950/20 px-3 py-2 text-sm text-emerald-200">{actionMessage}</p>
        ) : null}
        <div className="mt-4 flex gap-3">
          <button
            className="btn-primary"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              setActionMessage("");
              try {
                const result = await api.post<{
                  run_id?: string;
                  queued?: boolean;
                  task_id?: string | null;
                  manual_approval_required?: boolean;
                }>(`/campaigns/${params.id}/launch`, {});
                setActionMessage(
                  result.queued
                    ? "Worker run queued. Monitor Worker Runs for progress."
                    : "Campaign launch executed immediately."
                );
                await load();
              } finally {
                setBusy(false);
              }
            }}
          >
            Start Mission
          </button>
          <button
            className="btn-secondary"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try {
                await api.post(`/campaigns/${params.id}/pause`, {});
                setActionMessage("Mission paused.");
                await load();
              } finally {
                setBusy(false);
              }
            }}
          >
            Pause Mission
          </button>
        </div>
      </div>
      <div className="card p-4">
        <h3 className="text-base font-semibold">Approval Queue</h3>
        <div className="mt-3 space-y-3">
          {messages.length === 0 ? (
            <p className="text-sm text-slate-600">No messages generated yet. Start the mission to draft outreach.</p>
          ) : (
            messages.map((message) => (
              <div key={message.id} className="rounded-lg border border-slate-200/70 bg-slate-900/35 p-3">
                <div className="flex items-center justify-between">
                  <p className="font-medium">{message.subject_line}</p>
                  <StatusBadge status={message.approval_status} />
                </div>
                <p className="mt-1 whitespace-pre-line text-sm text-slate-600">{message.body_text}</p>
                <div className="mt-2 flex gap-2">
                  <button
                    className="btn-secondary"
                    disabled={busy}
                    onClick={async () => {
                      setBusy(true);
                      try {
                        await api.post(`/messages/${message.id}/approve`, {});
                        await load();
                      } finally {
                        setBusy(false);
                      }
                    }}
                  >
                    Approve
                  </button>
                  <button
                    className="btn-secondary"
                    disabled={busy}
                    onClick={async () => {
                      setBusy(true);
                      try {
                        await api.post(`/messages/${message.id}/reject`, {});
                        await load();
                      } finally {
                        setBusy(false);
                      }
                    }}
                  >
                    Reject
                  </button>
                  <button
                    className="btn-secondary"
                    disabled={busy}
                    onClick={async () => {
                      setBusy(true);
                      try {
                        await api.post(`/messages/${message.id}/regenerate`, {});
                        await load();
                      } finally {
                        setBusy(false);
                      }
                    }}
                  >
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
