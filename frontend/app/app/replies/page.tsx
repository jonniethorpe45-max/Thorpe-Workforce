"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/services/api";
import type { Reply } from "@/types";

export default function RepliesPage() {
  const [replies, setReplies] = useState<Reply[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<Reply[]>("/replies")
      .then(setReplies)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load replies"));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!replies) return <LoadingState label="Loading replies..." />;
  if (!replies.length) {
    return <EmptyState title="No replies yet" description="Interested replies and objections will appear here." />;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Interested Replies Inbox</h2>
      <div className="space-y-3">
        {replies.map((reply) => (
          <div className="card p-4" key={reply.id}>
            <div className="flex items-center justify-between">
              <StatusBadge status={reply.intent_classification} />
              <span className="text-xs text-slate-500">{new Date(reply.created_at).toLocaleString()}</span>
            </div>
            <p className="mt-2 text-sm text-slate-700">{reply.reply_text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
