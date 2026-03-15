"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { api } from "@/services/api";
import type { FounderOSChainRunResponse, FounderOSOverviewRead } from "@/types";

function asNumber(value: unknown): number {
  if (typeof value === "number") return value;
  return Number(value ?? 0) || 0;
}

export default function FounderOSOverviewPage() {
  const [overview, setOverview] = useState<FounderOSOverviewRead | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busyChainId, setBusyChainId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError("");
    const payload = await api.get<FounderOSOverviewRead>("/founder-os/overview");
    setOverview(payload);
  }, []);

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load Founder OS overview"));
  }, [load]);

  const runChainNow = async (chainId: string) => {
    try {
      setBusyChainId(chainId);
      setError("");
      const response = await api.post<FounderOSChainRunResponse>(`/founder-os/chains/${chainId}/run`, {
        runtime_input: {},
        use_prefill_context: true
      });
      setMessage(`Run completed (${response.status}). Report created.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run founder chain");
    } finally {
      setBusyChainId(null);
    }
  };

  if (error && !overview) return <ErrorState message={error} />;
  if (!overview) return <LoadingState label="Loading Founder OS..." />;

  const metrics = overview.metrics_snapshot || {};

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-2xl font-semibold">Founder OS</h2>
          <p className="text-sm text-slate-600">Run your startup with AI workers using the internal worker stack.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link className="btn-secondary" href="/app/founder-os/chains">
            Founder Chains
          </Link>
          <Link className="btn-secondary" href="/app/founder-os/reports">
            Reports
          </Link>
          <Link className="btn-secondary" href="/app/founder-os/automations">
            Automations
          </Link>
        </div>
      </div>

      {error ? <ErrorState message={error} /> : null}
      {message ? <div className="card border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</div> : null}

      <div className="grid gap-3 md:grid-cols-4">
        <div className="card p-4">
          <p className="text-xs text-slate-500">Runs (7d)</p>
          <p className="text-2xl font-semibold">{asNumber(metrics.runs_last_7_days)}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-slate-500">Installs (7d)</p>
          <p className="text-2xl font-semibold">{asNumber(metrics.installs_last_7_days)}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-slate-500">New Users (7d)</p>
          <p className="text-2xl font-semibold">{asNumber(metrics.new_users_last_7_days)}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-slate-500">Revenue (month est.)</p>
          <p className="text-2xl font-semibold">${(asNumber(metrics.estimated_revenue_month_cents) / 100).toFixed(2)}</p>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card p-4">
          <h3 className="text-base font-semibold">Featured Founder Chains</h3>
          <ul className="mt-3 space-y-3 text-sm">
            {overview.available_chains.slice(0, 3).map((chain) => (
              <li key={chain.id} className="rounded-lg border border-slate-200 p-3">
                <div className="flex items-center justify-between gap-2">
                  <div>
                    <p className="font-medium">{chain.name}</p>
                    <p className="text-xs text-slate-500">{chain.description}</p>
                  </div>
                  <button
                    className="btn-primary px-3 py-1 text-xs"
                    disabled={busyChainId === chain.id}
                    onClick={() => runChainNow(chain.id)}
                  >
                    {busyChainId === chain.id ? "Running..." : "Run Now"}
                  </button>
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  Last report: {chain.last_report_created_at ? new Date(chain.last_report_created_at).toLocaleString() : "none"}
                </p>
              </li>
            ))}
          </ul>
        </div>

        <div className="card p-4">
          <h3 className="text-base font-semibold">Recommended Next Actions</h3>
          <ul className="mt-3 list-inside list-disc space-y-2 text-sm text-slate-700">
            {overview.recommended_next_actions.length === 0 ? (
              <li>No recommendations available yet.</li>
            ) : (
              overview.recommended_next_actions.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)
            )}
          </ul>
          <div className="mt-4">
            <h4 className="text-sm font-semibold">Active Automations</h4>
            {overview.active_automations.length === 0 ? (
              <p className="mt-2 text-sm text-slate-600">No recurring automations enabled yet.</p>
            ) : (
              <ul className="mt-2 space-y-1 text-sm text-slate-700">
                {overview.active_automations.map((automation) => (
                  <li key={automation.id}>
                    {automation.chain_name} • {automation.frequency} • next{" "}
                    {automation.next_run_at ? new Date(automation.next_run_at).toLocaleString() : "unscheduled"}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>

      <div className="card p-4">
        <h3 className="text-base font-semibold">Latest Founder Reports</h3>
        {!overview.latest_reports.length ? (
          <EmptyState title="No Founder OS reports yet" description="Run any founder chain to create your first report." />
        ) : (
          <ul className="mt-3 space-y-2 text-sm">
            {overview.latest_reports.map((report) => (
              <li key={report.id} className="flex items-center justify-between gap-2 rounded-lg border border-slate-200 px-3 py-2">
                <div>
                  <p className="font-medium">{report.title}</p>
                  <p className="text-xs text-slate-500">
                    {report.report_type} • {new Date(report.created_at).toLocaleString()}
                  </p>
                </div>
                <Link className="text-brand-600 hover:underline" href={`/app/founder-os/reports/${report.id}`}>
                  View
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
