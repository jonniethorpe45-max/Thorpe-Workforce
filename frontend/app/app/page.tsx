"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
import { api } from "@/services/api";

type Overview = {
  active_workers: number;
  campaigns: number;
  leads_found: number;
  leads_researched: number;
  messages_awaiting_approval: number;
  emails_sent: number;
  replies: number;
  interested_replies: number;
  meetings_booked: number;
  recent_activity: Array<{ event_name: string; created_at: string }>;
  recent_worker_runs: Array<{
    run_id: string;
    worker_id: string;
    worker_name: string;
    status: string;
    started_at: string;
    finished_at?: string | null;
    campaign_id?: string | null;
  }>;
};

type OnboardingState = {
  is_completed: boolean;
  is_skipped: boolean;
  current_step: string;
};

export default function AppDashboardPage() {
  const [data, setData] = useState<Overview | null>(null);
  const [onboarding, setOnboarding] = useState<OnboardingState | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.get<Overview>("/analytics/overview"), api.get<OnboardingState>("/onboarding/state")])
      .then(([overview, onboardingState]) => {
        setData(overview);
        setOnboarding(onboardingState);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load analytics"));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState label="Loading dashboard metrics..." />;

  const onboarding = [
    { label: "Create AI Sales Worker", done: data.active_workers > 0, href: "/app/workers/new" },
    { label: "Create Campaign Mission", done: data.campaigns > 0, href: "/app/campaigns/new" },
    { label: "Add Leads", done: data.leads_found > 0, href: "/app/leads" },
    { label: "Review Approval Queue", done: data.messages_awaiting_approval > 0, href: "/app/campaigns" },
    { label: "Send First Email Batch", done: data.emails_sent > 0, href: "/app/campaigns" }
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Worker Mission Control</h2>
        <p className="text-sm text-slate-600">Track AI Sales Worker activity, approval queue health, and outcomes.</p>
      </div>
      {onboarding && !onboarding.is_completed && !onboarding.is_skipped ? (
        <div className="card border-brand-200 bg-brand-50 p-4">
          <p className="text-sm text-brand-900">
            Finish onboarding to activate your first worker flow. Current step: <strong>{onboarding.current_step}</strong>
          </p>
          <Link href="/app/onboarding" className="mt-2 inline-block text-sm font-medium text-brand-700 hover:underline">
            Resume onboarding →
          </Link>
        </div>
      ) : null}
      <section className="grid gap-4 md:grid-cols-3">
        <StatCard label="Active Workers" value={data.active_workers} />
        <StatCard label="Missions" value={data.campaigns} />
        <StatCard label="Leads in Workspace" value={data.leads_found} />
        <StatCard label="Leads Researched" value={data.leads_researched} />
        <StatCard label="Awaiting Approval" value={data.messages_awaiting_approval} />
        <StatCard label="Emails Sent" value={data.emails_sent} />
        <StatCard label="Replies Received" value={data.replies} />
        <StatCard label="Interested Replies" value={data.interested_replies} />
        <StatCard label="Meetings Booked" value={data.meetings_booked} />
      </section>
      <section className="card p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold">First-Run Checklist</h3>
          <span className="text-xs text-slate-500">
            {onboarding.filter((item) => item.done).length}/{onboarding.length} completed
          </span>
        </div>
        <ul className="mt-3 space-y-2 text-sm">
          {onboarding.map((item) => (
            <li key={item.label} className="flex items-center justify-between rounded-md border border-slate-200 px-3 py-2">
              <span className={item.done ? "text-emerald-700" : "text-slate-700"}>
                {item.done ? "✓" : "○"} {item.label}
              </span>
              <Link href={item.href} className="text-brand-600 hover:underline">
                Open
              </Link>
            </li>
          ))}
        </ul>
      </section>
      <section className="card p-4">
        <h3 className="text-base font-semibold">Recent Worker Runs</h3>
        <ul className="mt-3 space-y-2 text-sm text-slate-700">
          {data.recent_worker_runs.length === 0 ? (
            <li>No runs yet. Launch a campaign mission to start worker activity.</li>
          ) : (
            data.recent_worker_runs.map((run) => (
              <li key={run.run_id} className="rounded-md border border-slate-200 px-3 py-2">
                <p className="font-medium">
                  {run.worker_name} • {run.status}
                </p>
                <p className="text-xs text-slate-500">{new Date(run.started_at).toLocaleString()}</p>
              </li>
            ))
          )}
        </ul>
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
