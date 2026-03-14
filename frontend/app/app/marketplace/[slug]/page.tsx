"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/services/api";
import type { MarketplaceInstallResponse, MarketplaceWorkerDetailRead } from "@/types";

const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function formatPricing(priceCents: number, pricingType: string, currency: string): string {
  if (pricingType === "free") return "Free";
  if (pricingType === "internal") return "Internal";
  return `${(priceCents / 100).toFixed(2)} ${currency.toUpperCase()}`;
}

export default function MarketplaceDetailPage() {
  const params = useParams<{ slug: string }>();
  const [detail, setDetail] = useState<MarketplaceWorkerDetailRead | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const slug = params.slug;

  const load = useCallback(async () => {
    setError("");
    const endpoint = uuidPattern.test(slug) ? `/marketplace/templates/${slug}` : `/marketplace/templates/slug/${slug}`;
    const data = await api.get<MarketplaceWorkerDetailRead>(endpoint);
    setDetail(data);
  }, [slug]);

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load marketplace template"));
  }, [load]);

  const install = async () => {
    if (!detail) return;
    try {
      setBusy(true);
      setError("");
      const response = await api.post<MarketplaceInstallResponse>(`/marketplace/templates/${detail.template.id}/install`, {
        instance_name: `${detail.template.display_name} Instance`,
        runtime_config_overrides: {},
        memory_scope: "instance"
      });
      setMessage(response.message || "Installed marketplace worker.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to install template");
    } finally {
      setBusy(false);
    }
  };

  if (error && !detail) return <ErrorState message={error} />;
  if (!detail) return <LoadingState label="Loading marketplace detail..." />;

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h2 className="text-2xl font-semibold">{detail.template.display_name}</h2>
            <p className="text-sm text-slate-600">
              {detail.template.worker_type} • {detail.template.category}
            </p>
          </div>
          <StatusBadge status={detail.template.status} />
        </div>

        <p className="mt-3 text-sm text-slate-700">{detail.template.description || detail.template.short_description}</p>
        <p className="mt-2 text-sm text-slate-700">
          <span className="font-medium">Pricing:</span>{" "}
          {formatPricing(detail.template.price_cents, detail.template.pricing_type, detail.template.currency)}
        </p>
        <p className="text-sm text-slate-700">
          <span className="font-medium">Ratings:</span> ★ {detail.average_rating.toFixed(1)} ({detail.template.rating_count} reviews)
        </p>
        <p className="text-sm text-slate-700">
          <span className="font-medium">Installs:</span> {detail.installs}
        </p>

        <div className="mt-4 flex gap-2">
          <button className="btn-primary" disabled={detail.is_installed || busy} onClick={install}>
            {detail.is_installed ? "Installed" : busy ? "Installing..." : "Install Worker"}
          </button>
          <button className="btn-secondary" onClick={() => load().catch(() => undefined)}>
            Refresh
          </button>
        </div>
        {message ? <p className="mt-2 text-sm text-emerald-700">{message}</p> : null}
      </div>

      {error ? <ErrorState message={error} /> : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card p-4">
          <h3 className="text-base font-semibold">Included Tools</h3>
          <ul className="mt-2 space-y-2 text-sm text-slate-700">
            {detail.tools.length === 0 ? (
              <li>No tools configured.</li>
            ) : (
              detail.tools.map((tool) => (
                <li key={tool.id} className="rounded border border-slate-200 px-3 py-2">
                  <p className="font-medium">{tool.name}</p>
                  <p className="text-xs text-slate-500">{tool.slug}</p>
                </li>
              ))
            )}
          </ul>
        </div>
        <div className="card p-4">
          <h3 className="text-base font-semibold">Reviews</h3>
          <ul className="mt-2 space-y-2 text-sm text-slate-700">
            {detail.reviews.length === 0 ? (
              <li>No reviews yet.</li>
            ) : (
              detail.reviews.map((review) => (
                <li key={review.id} className="rounded border border-slate-200 px-3 py-2">
                  <p className="font-medium">Rating: {review.rating}/5</p>
                  <p>{review.review_text || "No review text"}</p>
                </li>
              ))
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}
