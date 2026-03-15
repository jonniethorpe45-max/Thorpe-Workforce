"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { PublicFooter } from "@/components/layout/PublicFooter";
import { PublicNav } from "@/components/layout/PublicNav";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { WorkerTemplateCard } from "@/components/ui/WorkerTemplateCard";
import type { PublicWorkerListItem } from "@/types";

function formatPricing(item: PublicWorkerListItem): string {
  if (item.pricing_type === "free") return "Free";
  if (item.pricing_type === "internal") return "Internal";
  return `${(item.price_cents / 100).toFixed(2)} ${item.currency.toUpperCase()}`;
}

export default function PublicWorkersPage() {
  const [workers, setWorkers] = useState<PublicWorkerListItem[] | null>(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [pricingType, setPricingType] = useState("");
  const [featuredOnly, setFeaturedOnly] = useState(false);
  const [sortBy, setSortBy] = useState("featured");

  useEffect(() => {
    const params = new URLSearchParams();
    if (search.trim()) params.set("search", search.trim());
    if (category) params.set("category", category);
    if (pricingType) params.set("pricing_type", pricingType);
    if (featuredOnly) params.set("featured_only", "true");
    if (sortBy) params.set("sort_by", sortBy);
    const loadWorkers = async () => {
      setError("");
      const response = await fetch(`/api/public/workers${params.toString() ? `?${params.toString()}` : ""}`, {
        cache: "no-store"
      });
      const payload = await response.json().catch(() => null);
      if (!response.ok) {
        const detail = (payload as { detail?: string } | null)?.detail;
        throw new Error(detail || "Failed to load public workers");
      }
      setWorkers(Array.isArray(payload) ? (payload as PublicWorkerListItem[]) : []);
    };
    loadWorkers().catch((err) => {
      setError(err instanceof Error ? err.message : "Failed to load public workers");
      setWorkers([]);
    });
  }, [category, featuredOnly, pricingType, search, sortBy]);

  return (
    <div className="min-h-screen bg-slate-50">
      <PublicNav />
      <main className="mx-auto max-w-6xl space-y-6 px-6 py-10">
        <div>
          <Link href="/" className="text-sm font-medium text-brand-600 hover:underline">
            ← Back to Home
          </Link>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-700">Thorpe Workforce</p>
            <h1 className="text-3xl font-semibold text-slate-900">Public Worker Library</h1>
            <p className="text-sm text-slate-600">Discover marketplace-ready worker templates and their capabilities.</p>
          </div>
        </div>

        {error ? <ErrorState message={error} /> : null}

        <div className="card grid gap-3 p-4 md:grid-cols-5">
          <input
            className="rounded-lg border border-slate-200 px-3 py-2 text-sm"
            placeholder="Search workers"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select className="rounded-lg border border-slate-200 px-3 py-2 text-sm" value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">All categories</option>
            <option value="real_estate">Real Estate</option>
            <option value="marketing">Marketing</option>
            <option value="content">Content</option>
            <option value="sales">Sales</option>
            <option value="research">Research</option>
            <option value="operations">Operations</option>
            <option value="automation">Automation</option>
          </select>
          <select className="rounded-lg border border-slate-200 px-3 py-2 text-sm" value={pricingType} onChange={(e) => setPricingType(e.target.value)}>
            <option value="">All pricing</option>
            <option value="free">Free</option>
            <option value="one_time">One-time</option>
            <option value="subscription">Subscription</option>
          </select>
          <select className="rounded-lg border border-slate-200 px-3 py-2 text-sm" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="featured">Featured</option>
            <option value="top">Top</option>
            <option value="new">New</option>
            <option value="rating">Rating</option>
            <option value="price_low">Price: Low</option>
            <option value="price_high">Price: High</option>
          </select>
          <label className="inline-flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={featuredOnly} onChange={(e) => setFeaturedOnly(e.target.checked)} />
            Featured only
          </label>
        </div>

        {!workers ? (
          <LoadingState label="Loading public worker library..." />
        ) : !workers.length ? (
          <EmptyState title="No public workers yet" description="Public templates will appear here when published." />
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {workers.map((worker) => (
              <WorkerTemplateCard
                key={worker.id}
                name={worker.name}
                category={worker.category}
                description={worker.short_description || "No summary provided."}
                pricingLabel={formatPricing(worker)}
                ratingLabel={`★ ${worker.rating_avg.toFixed(1)} (${worker.rating_count})`}
                installsLabel={`${worker.install_count} installs`}
                tags={worker.tags_json}
                isFeatured={worker.is_featured}
                footer={
                  <Link className="btn-secondary px-3 py-1 text-xs" href={`/workers/${worker.slug}`}>
                    View Worker Details
                  </Link>
                }
              />
            ))}
          </div>
        )}
      </main>
      <PublicFooter />
    </div>
  );
}
