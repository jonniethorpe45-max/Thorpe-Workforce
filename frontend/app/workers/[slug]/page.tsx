"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { PublicFooter } from "@/components/layout/PublicFooter";
import { PublicNav } from "@/components/layout/PublicNav";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import type { PublicWorkerDetailRead } from "@/types";

function formatPricing(pricingType: string, priceCents: number, currency: string): string {
  if (pricingType === "free") return "Free";
  if (pricingType === "internal") return "Internal";
  return `${(priceCents / 100).toFixed(2)} ${currency.toUpperCase()}`;
}

export default function PublicWorkerDetailPage() {
  const params = useParams<{ slug: string }>();
  const [detail, setDetail] = useState<PublicWorkerDetailRead | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadDetail = async () => {
      setError("");
      const response = await fetch(`/api/public/workers/${params.slug}`, { cache: "no-store" });
      const payload = await response.json().catch(() => null);
      if (!response.ok) {
        const detail = (payload as { detail?: string } | null)?.detail;
        throw new Error(detail || "Failed to load public worker");
      }
      setDetail(payload as PublicWorkerDetailRead);
    };
    loadDetail().catch((err) => setError(err instanceof Error ? err.message : "Failed to load public worker"));
  }, [params.slug]);

  if (error && !detail) {
    return (
      <div className="min-h-screen bg-slate-50">
        <PublicNav />
        <main className="mx-auto max-w-4xl space-y-4 px-6 py-12">
          <Link href="/" className="text-sm font-medium text-brand-600 hover:underline">
            ← Back to Home
          </Link>
          <ErrorState message={error} />
        </main>
        <PublicFooter />
      </div>
    );
  }
  if (!detail) {
    return (
      <div className="min-h-screen bg-slate-50">
        <PublicNav />
        <main className="mx-auto max-w-4xl space-y-4 px-6 py-12">
          <Link href="/" className="text-sm font-medium text-brand-600 hover:underline">
            ← Back to Home
          </Link>
          <LoadingState label="Loading worker details..." />
        </main>
        <PublicFooter />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <PublicNav />
      <main className="mx-auto max-w-4xl space-y-5 px-6 py-10">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <Link className="text-sm font-medium text-brand-600 hover:underline" href="/workers">
            ← Back to Public Worker Library
          </Link>
          <Link className="btn-primary" href="/signup">
            Deploy This Worker
          </Link>
        </div>

        <section className="card p-5">
          <h1 className="text-3xl font-semibold">{detail.template.display_name}</h1>
          <p className="mt-1 text-sm text-slate-600">
            {detail.template.worker_type} • {detail.template.category}
          </p>
          <p className="mt-3 text-sm text-slate-700">{detail.template.description || detail.template.short_description}</p>

          <div className="mt-4 grid gap-2 text-sm md:grid-cols-2">
            <p>
              <span className="font-medium">Pricing:</span>{" "}
              {formatPricing(detail.template.pricing_type, detail.template.price_cents, detail.template.currency)}
            </p>
            <p>
              <span className="font-medium">Rating:</span> ★ {detail.average_rating.toFixed(1)} ({detail.template.rating_count})
            </p>
            <p>
              <span className="font-medium">Installs:</span> {detail.installs}
            </p>
            <p>
              <span className="font-medium">Status:</span> {detail.template.status}
            </p>
          </div>

          {detail.template.tags_json?.length ? (
            <div className="mt-4 flex flex-wrap gap-1">
              {detail.template.tags_json.map((tag) => (
                <span className="rounded-full bg-brand-50 px-2 py-1 text-xs text-brand-700" key={`${detail.template.id}-${tag}`}>
                  {tag}
                </span>
              ))}
            </div>
          ) : null}
        </section>

        <section className="grid gap-4 md:grid-cols-2">
          <div className="card p-4">
            <h2 className="text-base font-semibold">Available Tools</h2>
            <ul className="mt-2 space-y-2 text-sm text-slate-700">
              {detail.tools.length === 0 ? (
                <li>No tools configured.</li>
              ) : (
                detail.tools.map((tool) => (
                  <li className="rounded border border-slate-200 px-3 py-2" key={tool.id}>
                    <p className="font-medium">{tool.name}</p>
                    <p className="text-xs text-slate-500">{tool.slug}</p>
                    {tool.description ? <p className="text-xs text-slate-600">{tool.description}</p> : null}
                  </li>
                ))
              )}
            </ul>
          </div>
          <div className="card p-4">
            <h2 className="text-base font-semibold">Recent Reviews</h2>
            <ul className="mt-2 space-y-2 text-sm text-slate-700">
              {detail.reviews.length === 0 ? (
                <li>No reviews yet.</li>
              ) : (
                detail.reviews.map((review) => (
                  <li className="rounded border border-slate-200 px-3 py-2" key={review.id}>
                    <p className="font-medium">Rating: {review.rating}/5</p>
                    <p>{review.review_text || "No review text."}</p>
                  </li>
                ))
              )}
            </ul>
          </div>
        </section>
      </main>
      <PublicFooter />
    </div>
  );
}
