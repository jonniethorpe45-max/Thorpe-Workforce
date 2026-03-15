"use client";

import { useEffect, useState } from "react";
import { CreditCard, DollarSign, TrendingDown } from "lucide-react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatCard } from "@/components/ui/StatCard";
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
      <h2 className="section-title">Admin Billing Summary</h2>
      {error ? <ErrorState message={error} /> : null}
      <div className="kpi-grid">
        <StatCard
          label="Estimated Platform Revenue"
          value={`$${(summary.estimated_platform_revenue / 100).toFixed(2)}`}
          icon={<DollarSign className="h-4 w-4" />}
        />
        <StatCard label="Churned Subscriptions" value={summary.churned_subscriptions_count} icon={<TrendingDown className="h-4 w-4" />} />
        <StatCard label="Failed Payments" value={summary.failed_payments_count} icon={<CreditCard className="h-4 w-4" />} />
      </div>

      <div className="card p-4">
        <h3 className="text-base font-semibold">Active Subscriptions by Plan</h3>
        <ul className="mt-2 space-y-1 text-sm">
          {Object.entries(summary.active_subscriptions_by_plan).map(([plan, count]) => (
            <li key={plan} className="flex items-center justify-between rounded-lg border border-slate-200/60 bg-slate-900/35 px-3 py-1.5">
              <span className="chip">{plan}</span>
              <span className="font-semibold text-slate-700">{count}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
