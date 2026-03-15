"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Compass, Search, Sparkles, TrendingUp } from "lucide-react";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { WorkerTemplateCard } from "@/components/ui/WorkerTemplateCard";
import { api } from "@/services/api";
import type { BillingCheckoutSessionResponse, MarketplaceInstallResponse, MarketplaceListingRead } from "@/types";

function formatPricing(priceCents: number, pricingType: string, currency: string): string {
  if (pricingType === "free") return "Free";
  if (pricingType === "internal") return "Internal";
  return `${(priceCents / 100).toFixed(2)} ${currency.toUpperCase()}`;
}

export default function MarketplacePage() {
  const [listings, setListings] = useState<MarketplaceListingRead[] | null>(null);
  const [categoryFilter, setCategoryFilter] = useState("");
  const [tagFilter, setTagFilter] = useState("");
  const [pricingFilter, setPricingFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState("featured");
  const [featuredOnly, setFeaturedOnly] = useState(false);
  const [busyTemplateId, setBusyTemplateId] = useState<string | null>(null);
  const [checkoutBusyTemplateId, setCheckoutBusyTemplateId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    setError("");
    const query = new URLSearchParams();
    if (categoryFilter.trim()) query.set("category", categoryFilter.trim());
    if (tagFilter.trim()) query.set("tag", tagFilter.trim());
    if (pricingFilter !== "all") query.set("pricing_type", pricingFilter);
    if (search.trim()) query.set("search", search.trim());
    if (sortBy) query.set("sort_by", sortBy);
    if (featuredOnly) query.set("featured_only", "true");
    const path = query.toString() ? `/marketplace/templates?${query.toString()}` : "/marketplace/templates";
    const data = await api.get<MarketplaceListingRead[]>(path);
    setListings(data);
  }, [categoryFilter, featuredOnly, pricingFilter, search, sortBy, tagFilter]);

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load marketplace templates"));
  }, [load]);

  const installTemplate = async (templateId: string, templateName: string) => {
    try {
      setBusyTemplateId(templateId);
      setError("");
      const response = await api.post<MarketplaceInstallResponse>(`/marketplace/templates/${templateId}/install`, {
        instance_name: `${templateName} Instance`,
        runtime_config_overrides: {},
        memory_scope: "instance"
      });
      setMessage(response.message || "Template installed.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to install marketplace template");
    } finally {
      setBusyTemplateId(null);
    }
  };

  const checkoutTemplate = async (templateId: string) => {
    try {
      setCheckoutBusyTemplateId(templateId);
      setError("");
      const response = await api.post<BillingCheckoutSessionResponse>(`/billing/checkout/worker/${templateId}`, {});
      if (response.checkout_url) {
        window.location.href = response.checkout_url;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create checkout session");
    } finally {
      setCheckoutBusyTemplateId(null);
    }
  };

  if (error && !listings) return <ErrorState message={error} />;
  if (!listings) return <LoadingState label="Loading marketplace..." />;

  return (
    <div className="space-y-5">
      <div>
        <h2 className="section-title">Worker Marketplace</h2>
        <p className="section-subtitle">Discover premium AI workers, install instantly, and launch new automations fast.</p>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <div className="card p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Catalog size</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{listings.length}</p>
          <p className="mt-1 text-xs text-slate-600">Workers matching your filters.</p>
        </div>
        <div className="card p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Featured now</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{listings.filter((item) => item.template.is_featured).length}</p>
          <p className="mt-1 text-xs text-slate-600">Curated workers with strong traction.</p>
        </div>
        <div className="card p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Install ready</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{listings.filter((item) => !item.is_installed).length}</p>
          <p className="mt-1 text-xs text-slate-600">Available for this workspace right now.</p>
        </div>
      </div>

      <div className="card grid gap-3 p-4 md:grid-cols-6">
        <label className="text-sm md:col-span-2">
          <span className="mb-1 inline-flex items-center gap-1 text-slate-600">
            <Search className="h-3.5 w-3.5" />
            Search
          </span>
          <input
            className="w-full rounded-lg border border-slate-200 px-3 py-2"
            onChange={(event) => setSearch(event.target.value)}
            placeholder="cold email, seo, real estate..."
            value={search}
          />
        </label>
        <label className="text-sm md:col-span-1">
          <span className="mb-1 block text-slate-600">Category</span>
          <input
            className="w-full rounded-lg border border-slate-200 px-3 py-2"
            onChange={(event) => setCategoryFilter(event.target.value)}
            placeholder="sales, support..."
            value={categoryFilter}
          />
        </label>
        <label className="text-sm md:col-span-1">
          <span className="mb-1 block text-slate-600">Tag</span>
          <input
            className="w-full rounded-lg border border-slate-200 px-3 py-2"
            onChange={(event) => setTagFilter(event.target.value)}
            placeholder="pipeline"
            value={tagFilter}
          />
        </label>
        <label className="text-sm md:col-span-1">
          <span className="mb-1 block text-slate-600">Pricing</span>
          <select
            className="w-full rounded-lg border border-slate-200 px-3 py-2"
            onChange={(event) => setPricingFilter(event.target.value)}
            value={pricingFilter}
          >
            <option value="all">all</option>
            <option value="free">free</option>
            <option value="subscription">subscription</option>
            <option value="one_time">one_time</option>
            <option value="internal">internal</option>
          </select>
        </label>
        <label className="text-sm md:col-span-1">
          <span className="mb-1 block text-slate-600">Sort</span>
          <select className="w-full rounded-lg border border-slate-200 px-3 py-2" value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
            <option value="featured">featured</option>
            <option value="top">top</option>
            <option value="trending">trending</option>
            <option value="new">new</option>
            <option value="rating">rating</option>
            <option value="price_low">price_low</option>
            <option value="price_high">price_high</option>
          </select>
        </label>
        <label className="inline-flex items-end gap-2 text-sm text-slate-700">
          <input type="checkbox" checked={featuredOnly} onChange={(event) => setFeaturedOnly(event.target.checked)} />
          Featured only
        </label>
        <div className="flex items-end">
          <button className="btn-secondary w-full" onClick={() => load().catch(() => undefined)}>
            Apply Filters
          </button>
        </div>
      </div>

      {error ? <ErrorState message={error} /> : null}
      {message ? <div className="card border-emerald-200/50 bg-emerald-950/20 p-3 text-sm text-emerald-200">{message}</div> : null}

      {listings.length ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="card p-4">
            <h3 className="inline-flex items-center gap-2 text-base font-semibold">
              <TrendingUp className="h-4 w-4 text-cyan-300" />
              Trending workers
            </h3>
            <ul className="mt-3 space-y-2 text-sm">
              {listings
                .slice()
                .sort((a, b) => (b.template.install_count || 0) - (a.template.install_count || 0))
                .slice(0, 4)
                .map((item) => (
                  <li key={`trending-${item.template.id}`} className="flex items-center justify-between rounded-lg border border-slate-200/60 bg-slate-900/45 px-3 py-2">
                    <div>
                      <p className="font-medium text-slate-900">{item.template.display_name}</p>
                      <p className="text-xs text-slate-500">{item.template.category}</p>
                    </div>
                    <span className="chip">{item.template.install_count} installs</span>
                  </li>
                ))}
            </ul>
          </div>
          <div className="card p-4">
            <h3 className="inline-flex items-center gap-2 text-base font-semibold">
              <Compass className="h-4 w-4 text-indigo-300" />
              Featured collection
            </h3>
            <ul className="mt-3 space-y-2 text-sm">
              {listings
                .filter((item) => item.template.is_featured)
                .slice(0, 4)
                .map((item) => (
                  <li key={`featured-${item.template.id}`} className="flex items-center justify-between rounded-lg border border-slate-200/60 bg-slate-900/45 px-3 py-2">
                    <div>
                      <p className="font-medium text-slate-900">{item.template.display_name}</p>
                      <p className="text-xs text-slate-500">{item.template.short_description || item.template.category}</p>
                    </div>
                    <Sparkles className="h-4 w-4 text-cyan-300" />
                  </li>
                ))}
            </ul>
          </div>
        </div>
      ) : null}

      {!listings.length ? (
        <EmptyState title="No marketplace workers found" description="Adjust filters or publish templates to marketplace visibility." />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {listings.map((listing) => (
            <WorkerTemplateCard
              key={listing.template.id}
              name={listing.template.display_name}
              category={listing.template.category}
              description={listing.template.short_description || listing.template.description || "No description provided."}
              pricingLabel={formatPricing(listing.template.price_cents, listing.template.pricing_type, listing.template.currency)}
              ratingLabel={`★ ${listing.template.rating_avg.toFixed(1)} (${listing.template.rating_count})`}
              installsLabel={`${listing.template.install_count} installs`}
              tags={listing.template.tags_json}
              isFeatured={listing.template.is_featured}
              status={<StatusBadge status={listing.template.status} />}
              footer={
                <>
                  <Link className="btn-secondary px-3 py-1 text-xs" href={`/app/marketplace/${listing.template.slug || listing.template.id}`}>
                    View Details
                  </Link>
                  <button
                    className="btn-primary px-3 py-1 text-xs"
                    disabled={
                      Boolean(listing.is_installed) ||
                      busyTemplateId === listing.template.id ||
                      checkoutBusyTemplateId === listing.template.id
                    }
                    onClick={() => {
                      if (listing.purchase_required) {
                        checkoutTemplate(listing.template.id).catch(() => undefined);
                        return;
                      }
                      installTemplate(listing.template.id, listing.template.display_name).catch(() => undefined);
                    }}
                  >
                    {listing.is_installed
                      ? "Installed"
                      : checkoutBusyTemplateId === listing.template.id
                        ? "Redirecting..."
                        : busyTemplateId === listing.template.id
                          ? "Installing..."
                          : listing.purchase_required
                            ? listing.template.pricing_type === "subscription"
                              ? "Subscribe to Install"
                              : "Buy to Install"
                            : "Install"}
                  </button>
                </>
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}
