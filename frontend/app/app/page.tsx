"use client";

import { useEffect, useState } from "react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { api } from "@/services/api";

type Overview = {
  active_workers: number;
  campaigns: number;
  leads_found: number;
  emails_sent: number;
  replies: number;
  meetings_booked: number;
  recent_activity: Array<{ event_name: string; created_at: string }>;
};

export default function AppDashboardPage() {
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<Overview>("/analytics/overview")
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load analytics"));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState label="Loading dashboard metrics..." />;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Overview</h2>
        <p className="text-sm text-slate-600">Monitor your AI sales workforce performance in real-time.</p>
      </div>
      <section className="grid gap-4 md:grid-cols-3">
        <StatCard label="Active Workers" value={data.active_workers} />
        <StatCard label="Campaigns" value={data.campaigns} />
        <StatCard label="Leads Found" value={data.leads_found} />
        <StatCard label="Emails Sent" value={data.emails_sent} />
        <StatCard label="Replies" value={data.replies} />
        <StatCard label="Meetings Booked" value={data.meetings_booked} />
      </section>
      <section className="card p-4">
        <h3 className="text-base font-semibold">Recent Activity</h3>
        <ul className="mt-3 space-y-2 text-sm text-slate-600">
          {data.recent_activity.length === 0 ? (
            <li>No activity yet.</li>
          ) : (
            data.recent_activity.map((item) => (
              <li key={`${item.event_name}-${item.created_at}`}>
                {item.event_name} • {new Date(item.created_at).toLocaleString()}
              </li>
            ))
          )}
        </ul>
      </section>
    </div>
  );
}
