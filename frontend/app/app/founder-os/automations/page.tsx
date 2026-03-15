"use client";

import { useCallback, useEffect, useState } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { api } from "@/services/api";
import type {
  FounderOSAutomationListResponse,
  FounderOSAutomationRead,
  FounderOSChainListResponse
} from "@/types";

type FormState = {
  chain_id: string;
  frequency: "daily" | "weekly" | "monthly";
  is_enabled: boolean;
  runtime_input_json: string;
};

const defaultForm: FormState = {
  chain_id: "",
  frequency: "weekly",
  is_enabled: true,
  runtime_input_json: "{}"
};

function parseJson(value: string): Record<string, unknown> {
  const parsed = JSON.parse(value || "{}");
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("runtime_input_json must be a JSON object");
  }
  return parsed as Record<string, unknown>;
}

export default function FounderOSAutomationsPage() {
  const [chains, setChains] = useState<FounderOSChainListResponse["items"]>([]);
  const [automations, setAutomations] = useState<FounderOSAutomationRead[] | null>(null);
  const [form, setForm] = useState<FormState>(defaultForm);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setError("");
    const [chainsRes, automationsRes] = await Promise.all([
      api.get<FounderOSChainListResponse>("/founder-os/chains"),
      api.get<FounderOSAutomationListResponse>("/founder-os/automations")
    ]);
    setChains(chainsRes.items);
    setAutomations(automationsRes.items);
    if (!form.chain_id && chainsRes.items[0]) {
      setForm((current) => ({ ...current, chain_id: chainsRes.items[0].id }));
    }
  }, [form.chain_id]);

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load automations"));
  }, [load]);

  const createAutomation = async () => {
    try {
      setBusy(true);
      setError("");
      await api.post<FounderOSAutomationRead>("/founder-os/automations", {
        chain_id: form.chain_id,
        frequency: form.frequency,
        is_enabled: form.is_enabled,
        runtime_input_json: parseJson(form.runtime_input_json)
      });
      setMessage("Automation created.");
      setForm((current) => ({ ...current, runtime_input_json: "{}" }));
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create automation");
    } finally {
      setBusy(false);
    }
  };

  const toggleAutomation = async (automation: FounderOSAutomationRead) => {
    try {
      setBusy(true);
      setError("");
      await api.patch<FounderOSAutomationRead>(`/founder-os/automations/${automation.id}`, {
        is_enabled: !automation.is_enabled
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update automation");
    } finally {
      setBusy(false);
    }
  };

  if (error && !automations) return <ErrorState message={error} />;
  if (!automations) return <LoadingState label="Loading founder automations..." />;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-semibold">Founder OS Automations</h2>
        <p className="text-sm text-slate-600">Set recurring metadata for founder chains (daily/weekly/monthly).</p>
      </div>

      {error ? <ErrorState message={error} /> : null}
      {message ? <div className="card border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</div> : null}

      <div className="card p-4">
        <h3 className="text-base font-semibold">Create Automation</h3>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <label className="text-sm">
            <span className="mb-1 block text-slate-600">Founder Chain</span>
            <select
              className="w-full rounded-lg border border-slate-200 px-3 py-2"
              onChange={(event) => setForm((current) => ({ ...current, chain_id: event.target.value }))}
              value={form.chain_id}
            >
              {chains.map((chain) => (
                <option key={chain.id} value={chain.id}>
                  {chain.name}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-slate-600">Frequency</span>
            <select
              className="w-full rounded-lg border border-slate-200 px-3 py-2"
              onChange={(event) => setForm((current) => ({ ...current, frequency: event.target.value as FormState["frequency"] }))}
              value={form.frequency}
            >
              <option value="daily">daily</option>
              <option value="weekly">weekly</option>
              <option value="monthly">monthly</option>
            </select>
          </label>
          <label className="text-sm md:col-span-2">
            <span className="mb-1 block text-slate-600">Runtime Input JSON</span>
            <textarea
              className="h-24 w-full rounded-lg border border-slate-200 px-3 py-2 font-mono text-xs"
              onChange={(event) => setForm((current) => ({ ...current, runtime_input_json: event.target.value }))}
              value={form.runtime_input_json}
            />
          </label>
          <label className="inline-flex items-center gap-2 text-sm text-slate-700">
            <input
              checked={form.is_enabled}
              onChange={(event) => setForm((current) => ({ ...current, is_enabled: event.target.checked }))}
              type="checkbox"
            />
            Enable immediately
          </label>
        </div>
        <button className="btn-primary mt-3" disabled={busy || !form.chain_id} onClick={createAutomation}>
          {busy ? "Saving..." : "Create Automation"}
        </button>
      </div>

      {!automations.length ? (
        <EmptyState title="No automations configured" description="Create your first recurring Founder OS automation above." />
      ) : (
        <div className="card p-0">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-100 text-left text-slate-600">
              <tr>
                <th className="px-4 py-3">Chain</th>
                <th className="px-4 py-3">Frequency</th>
                <th className="px-4 py-3">Enabled</th>
                <th className="px-4 py-3">Next Run</th>
                <th className="px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {automations.map((automation) => (
                <tr key={automation.id} className="border-t border-slate-200">
                  <td className="px-4 py-3">{automation.chain_name}</td>
                  <td className="px-4 py-3">{automation.frequency}</td>
                  <td className="px-4 py-3">{automation.is_enabled ? "Yes" : "No"}</td>
                  <td className="px-4 py-3">
                    {automation.next_run_at ? new Date(automation.next_run_at).toLocaleString() : "unscheduled"}
                  </td>
                  <td className="px-4 py-3">
                    <button className="text-brand-600 hover:underline" disabled={busy} onClick={() => toggleAutomation(automation)}>
                      {automation.is_enabled ? "Disable" : "Enable"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
