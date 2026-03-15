"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { api } from "@/services/api";
import type {
  BillingCheckoutSessionResponse,
  BillingEntitlementsRead,
  BillingPlanRead,
  BillingPortalResponse,
  BillingSubscriptionRead
} from "@/types";

function formatPrice(amountCents: number, interval: "monthly" | "annual") {
  if (amountCents <= 0) return "Free";
  const suffix = interval === "annual" ? "/yr" : "/mo";
  return `$${(amountCents / 100).toFixed(2)}${suffix}`;
}

export default function BillingSettingsPage() {
  const [plans, setPlans] = useState<BillingPlanRead[] | null>(null);
  const [subscription, setSubscription] = useState<BillingSubscriptionRead | null>(null);
  const [entitlements, setEntitlements] = useState<BillingEntitlementsRead | null>(null);
  const [interval, setInterval] = useState<"monthly" | "annual">("monthly");
  const [busyPlanCode, setBusyPlanCode] = useState<string | null>(null);
  const [portalBusy, setPortalBusy] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    const [plansRes, subscriptionRes, entitlementsRes] = await Promise.all([
      api.get<BillingPlanRead[]>("/billing/plans"),
      api.get<BillingSubscriptionRead>("/billing/subscription"),
      api.get<BillingEntitlementsRead>("/billing/entitlements")
    ]);
    setPlans(plansRes);
    setSubscription(subscriptionRes);
    setEntitlements(entitlementsRes);
  }, []);

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load billing data"));
  }, [load]);

  const currentPlanCode = entitlements?.plan.code ?? subscription?.plan_code ?? "";
  const visiblePlans = useMemo(() => (plans ?? []).filter((plan) => plan.is_active), [plans]);

  const checkoutSubscription = async (planCode: string) => {
    try {
      setBusyPlanCode(planCode);
      setError("");
      const result = await api.post<BillingCheckoutSessionResponse>("/billing/checkout/subscription", {
        plan_code: planCode,
        billing_interval: interval
      });
      if (result.checkout_url) {
        window.location.href = result.checkout_url;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start checkout");
    } finally {
      setBusyPlanCode(null);
    }
  };

  const openPortal = async () => {
    try {
      setPortalBusy(true);
      setError("");
      const result = await api.post<BillingPortalResponse>("/billing/portal", {});
      if (result.portal_url) {
        window.location.href = result.portal_url;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to open billing portal");
    } finally {
      setPortalBusy(false);
    }
  };

  if (!plans || !subscription || !entitlements) {
    return <LoadingState label="Loading billing..." />;
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="section-title">Billing & Plan</h2>
        <p className="text-sm text-slate-600">Manage your subscription, limits, and billing portal access.</p>
      </div>

      {error ? <ErrorState message={error} /> : null}

      <section className="card p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">Current Plan</p>
            <h3 className="text-xl font-semibold">{subscription.plan_name}</h3>
            <p className="text-sm text-slate-600">
              Status: <span className="font-medium">{subscription.status}</span> • Interval:{" "}
              <span className="font-medium">{subscription.billing_interval}</span>
            </p>
            <p className="text-sm text-slate-600">
              Renewal/Period End: {subscription.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString() : "n/a"}
            </p>
          </div>
          <button className="btn-secondary" disabled={portalBusy} onClick={() => openPortal().catch(() => undefined)}>
            {portalBusy ? "Opening..." : "Manage Billing"}
          </button>
        </div>
      </section>

      <section className="card p-5">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-lg font-semibold">Plans</h3>
          <div className="flex items-center gap-2 text-sm">
            <label className="inline-flex items-center gap-1">
              <input checked={interval === "monthly"} onChange={() => setInterval("monthly")} type="radio" />
              Monthly
            </label>
            <label className="inline-flex items-center gap-1">
              <input checked={interval === "annual"} onChange={() => setInterval("annual")} type="radio" />
              Annual
            </label>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {visiblePlans.map((plan) => {
            const priceCents = interval === "annual" ? plan.annual_price_cents ?? plan.monthly_price_cents * 12 : plan.monthly_price_cents;
            const isCurrent = plan.code === currentPlanCode;
            return (
              <article className="rounded-xl border border-slate-200/70 bg-slate-900/35 p-4" key={plan.id}>
                <h4 className="text-base font-semibold">{plan.name}</h4>
                <p className="mt-1 text-sm text-slate-600">{plan.description}</p>
                <p className="mt-3 text-xl font-bold">{formatPrice(priceCents, interval)}</p>
                <ul className="mt-3 space-y-1 text-xs text-slate-600">
                  <li>Drafts: {plan.max_worker_drafts ?? "Unlimited"}</li>
                  <li>Published Workers: {plan.max_published_workers ?? "Unlimited"}</li>
                  <li>Installs: {plan.max_worker_installs_per_workspace ?? "Unlimited"}</li>
                  <li>Runs / month: {plan.max_worker_runs_per_month ?? "Unlimited"}</li>
                  <li>Worker Builder: {plan.allow_worker_builder ? "Yes" : "No"}</li>
                  <li>Marketplace Publish: {plan.allow_marketplace_publishing ? "Yes" : "No"}</li>
                </ul>
                <button
                  className="btn-primary mt-4 w-full"
                  disabled={isCurrent || busyPlanCode === plan.code || plan.code === "free"}
                  onClick={() => checkoutSubscription(plan.code).catch(() => undefined)}
                >
                  {isCurrent ? "Current Plan" : busyPlanCode === plan.code ? "Redirecting..." : "Upgrade"}
                </button>
              </article>
            );
          })}
        </div>
      </section>

      <section className="card p-5">
        <h3 className="text-lg font-semibold">Entitlements</h3>
        <div className="mt-3 grid gap-2 text-sm md:grid-cols-2">
          <p>Worker Builder: <span className="chip">{entitlements.features.allow_worker_builder ? "Enabled" : "Disabled"}</span></p>
          <p>Marketplace Publishing: <span className="chip">{entitlements.features.allow_marketplace_publishing ? "Enabled" : "Disabled"}</span></p>
          <p>Public Workers: <span className="chip">{entitlements.features.allow_public_workers ? "Enabled" : "Disabled"}</span></p>
          <p>Marketplace Install: <span className="chip">{entitlements.features.allow_marketplace_install ? "Enabled" : "Disabled"}</span></p>
          <p>
            Worker Drafts: {entitlements.usage.worker_drafts} / {entitlements.limits.max_worker_drafts ?? "∞"}
          </p>
          <p>
            Published Workers: {entitlements.usage.published_workers} / {entitlements.limits.max_published_workers ?? "∞"}
          </p>
          <p>
            Worker Installs: {entitlements.usage.worker_installs} / {entitlements.limits.max_worker_installs_per_workspace ?? "∞"}
          </p>
          <p>
            Worker Runs (month): {entitlements.usage.worker_runs_month} / {entitlements.limits.max_worker_runs_per_month ?? "∞"}
          </p>
        </div>
      </section>
    </div>
  );
}
