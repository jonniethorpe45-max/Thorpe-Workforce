"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PublicFooter } from "@/components/layout/PublicFooter";
import { PublicNav } from "@/components/layout/PublicNav";
import { api } from "@/services/api";
import type { BillingPlanRead } from "@/types";

function formatPrice(plan: BillingPlanRead, interval: "monthly" | "annual") {
  const amount = interval === "annual" ? plan.annual_price_cents ?? plan.monthly_price_cents * 12 : plan.monthly_price_cents;
  if (amount <= 0) return "Free";
  return `$${(amount / 100).toFixed(2)}${interval === "annual" ? "/yr" : "/mo"}`;
}

export default function PricingPage() {
  const [plans, setPlans] = useState<BillingPlanRead[] | null>(null);
  const [interval, setInterval] = useState<"monthly" | "annual">("monthly");
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<BillingPlanRead[]>("/billing/plans")
      .then((items) => setPlans(items.filter((plan) => plan.is_active)))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load plans"));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      <PublicNav />
      <main className="mx-auto max-w-6xl px-6 py-16">
        <h1 className="text-4xl font-semibold text-slate-900">Pricing</h1>
        <p className="mt-2 text-slate-600">Choose the plan that matches your AI workforce goals.</p>
        <div className="mt-4 flex items-center gap-3 text-sm">
          <label className="inline-flex items-center gap-1">
            <input checked={interval === "monthly"} onChange={() => setInterval("monthly")} type="radio" />
            Monthly
          </label>
          <label className="inline-flex items-center gap-1">
            <input checked={interval === "annual"} onChange={() => setInterval("annual")} type="radio" />
            Annual
          </label>
        </div>

        {error ? <div className="mt-6"><ErrorState message={error} /></div> : null}
        {!plans ? (
          <div className="mt-8">
            <LoadingState label="Loading pricing..." />
          </div>
        ) : (
          <div className="mt-10 grid gap-6 md:grid-cols-2 xl:grid-cols-4">
            {plans.map((plan) => (
              <div key={plan.id} className="card p-6">
                <h2 className="text-xl font-semibold">{plan.name}</h2>
                <p className="mt-2 text-3xl font-bold">{formatPrice(plan, interval)}</p>
                <p className="mt-2 text-sm text-slate-600">{plan.description}</p>
                <ul className="mt-4 space-y-2 text-sm text-slate-600">
                  <li>Worker Builder: {plan.allow_worker_builder ? "Yes" : "No"}</li>
                  <li>Marketplace Publishing: {plan.allow_marketplace_publishing ? "Yes" : "No"}</li>
                  <li>Worker Drafts: {plan.max_worker_drafts ?? "Unlimited"}</li>
                  <li>Published Workers: {plan.max_published_workers ?? "Unlimited"}</li>
                  <li>Installs: {plan.max_worker_installs_per_workspace ?? "Unlimited"}</li>
                  <li>Runs / month: {plan.max_worker_runs_per_month ?? "Unlimited"}</li>
                </ul>
                <div className="mt-5">
                  {plan.code === "enterprise" ? (
                    <a className="btn-secondary" href="mailto:sales@thorpeworkforce.com">
                      Contact Sales
                    </a>
                  ) : (
                    <Link href="/signup" className="btn-primary">
                      Get Started
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-8 flex flex-wrap gap-2">
          <Link href="/app/settings/billing" className="btn-secondary">
            Manage Billing
          </Link>
          <Link href="/terms" className="btn-secondary">
            Terms
          </Link>
          <Link href="/privacy" className="btn-secondary">
            Privacy
          </Link>
        </div>
      </main>
      <PublicFooter />
    </div>
  );
}
