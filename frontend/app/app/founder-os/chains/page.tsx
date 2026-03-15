"use client";

import { useCallback, useEffect, useState } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { api } from "@/services/api";
import type { FounderOSChainListResponse, FounderOSChainRunResponse } from "@/types";

export default function FounderOSChainsPage() {
  const [chains, setChains] = useState<FounderOSChainListResponse["items"] | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busyChainId, setBusyChainId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError("");
    const response = await api.get<FounderOSChainListResponse>("/founder-os/chains");
    setChains(response.items);
  }, []);

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load founder chains"));
  }, [load]);

  const runNow = async (chainId: string) => {
    try {
      setBusyChainId(chainId);
      setError("");
      const result = await api.post<FounderOSChainRunResponse>(`/founder-os/chains/${chainId}/run`, {
        runtime_input: {},
        use_prefill_context: true
      });
      setMessage(`Chain run finished (${result.status}). Report saved.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run founder chain");
    } finally {
      setBusyChainId(null);
    }
  };

  if (error && !chains) return <ErrorState message={error} />;
  if (!chains) return <LoadingState label="Loading founder chains..." />;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-semibold">Founder OS Chains</h2>
        <p className="text-sm text-slate-600">Run repeatable founder workflows powered by the internal worker stack.</p>
      </div>
      {error ? <ErrorState message={error} /> : null}
      {message ? <div className="card border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</div> : null}

      {!chains.length ? (
        <EmptyState title="No founder chains available" description="Founder chain templates will appear once seeding is complete." />
      ) : (
        <div className="grid gap-4">
          {chains.map((chain) => (
            <div key={chain.id} className="card p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h3 className="text-lg font-semibold">{chain.name}</h3>
                  <p className="text-sm text-slate-600">{chain.description}</p>
                </div>
                <button className="btn-primary" disabled={busyChainId === chain.id} onClick={() => runNow(chain.id)}>
                  {busyChainId === chain.id ? "Running..." : "Run Now"}
                </button>
              </div>
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Workers Included</p>
                  <ul className="mt-1 space-y-1 text-sm text-slate-700">
                    {chain.workers.map((worker) => (
                      <li key={`${chain.id}-${worker.worker_template_id}`}>
                        {worker.name} <span className="text-xs text-slate-500">({worker.category})</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Expected Outputs</p>
                  <ul className="mt-1 list-inside list-disc space-y-1 text-sm text-slate-700">
                    {chain.expected_outputs.map((item) => (
                      <li key={`${chain.id}-${item}`}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
              <p className="mt-3 text-xs text-slate-500">
                Last report: {chain.last_report_created_at ? new Date(chain.last_report_created_at).toLocaleString() : "none"}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
