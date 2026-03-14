"use client";

import { useEffect, useState } from "react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { api } from "@/services/api";
import type { AdminBillingSummaryRead } from "@/types";

export default function AdminBillingPage() {
  const [summary, setSummary] = useState<AdminBillingSummaryRead | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<AdminBillingSummaryRead>("/admin/billing/summary")
      .then(setSummary)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load billing summary"));
  }, []);

  if (error && !summary) return <ErrorState message={error} />;
  if (!summary) return <LoadingState label="Loading billing analytics..." />;

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Admin Billing Summary</h2>
      {error ? <ErrorState message={error} /> : null}
      <div className="grid gap-3 md:grid-cols-3">
        <div className="card p-4"><p className="text-xs text-slate-500">Estimated Platform Revenue</p><p className="text-2xl font-semibold">${(summary.estimated_platform_revenue / 100).toFixed(2)}</p></div>
        <div className="card p-4"><p className="text-xs text-slate-500">Churned Subscriptions</p><p className="text-2xl font-semibold">{summary.churned_subscriptions_count}</p></div>
        <div className="card p-4"><p className="text-xs text-slate-500">Failed Payments</p><p className="text-2xl font-semibold">{summary.failed_payments_count}</p></div>
      </div>

      <div className="card p-4">
        <h3 className="text-base font-semibold">Active Subscriptions by Plan</h3>
        <ul className="mt-2 space-y-1 text-sm">
          {Object.entries(summary.active_subscriptions_by_plan).map(([plan, count]) => <li key={plan}>{plan}: {count}</li>)}
        </ul>
      </div>
    </div>
  );
}
