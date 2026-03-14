"use client";

import { FormEvent, useState } from "react";

type Payload = {
  worker_id?: string;
  name: string;
  ideal_customer_profile: string;
  target_industry: string;
  target_roles: string[];
  target_locations: string[];
  company_size_min?: number;
  company_size_max?: number;
  cta_text: string;
  exclusions: string[];
  scheduling_settings: Record<string, number>;
};

export function CampaignForm({
  workerOptions,
  onSubmit
}: {
  workerOptions: Array<{ id: string; name: string }>;
  onSubmit: (payload: Payload) => Promise<void>;
}) {
  const [payload, setPayload] = useState<Payload>({
    name: "",
    ideal_customer_profile: "",
    target_industry: "",
    target_roles: [],
    target_locations: [],
    cta_text: "Would you be open to a 15-minute intro next week?",
    exclusions: [],
    scheduling_settings: { step_2_delay_days: 3, step_3_delay_days: 7, step_4_delay_days: 12 }
  });
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await onSubmit(payload);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="card space-y-4 p-6" onSubmit={submit}>
      <h2 className="text-lg font-semibold">Create Campaign</h2>
      <input
        className="w-full rounded-lg border border-slate-200 px-3 py-2"
        placeholder="Campaign name"
        value={payload.name}
        onChange={(e) => setPayload((s) => ({ ...s, name: e.target.value }))}
        required
      />
      <select
        className="w-full rounded-lg border border-slate-200 px-3 py-2"
        value={payload.worker_id || ""}
        onChange={(e) => setPayload((s) => ({ ...s, worker_id: e.target.value || undefined }))}
      >
        <option value="">Assign worker (optional)</option>
        {workerOptions.map((worker) => (
          <option key={worker.id} value={worker.id}>
            {worker.name}
          </option>
        ))}
      </select>
      <textarea
        className="w-full rounded-lg border border-slate-200 px-3 py-2"
        placeholder="Ideal customer profile"
        value={payload.ideal_customer_profile}
        onChange={(e) => setPayload((s) => ({ ...s, ideal_customer_profile: e.target.value }))}
      />
      <div className="grid gap-4 md:grid-cols-2">
        <input
          className="rounded-lg border border-slate-200 px-3 py-2"
          placeholder="Target industry"
          value={payload.target_industry}
          onChange={(e) => setPayload((s) => ({ ...s, target_industry: e.target.value }))}
        />
        <input
          className="rounded-lg border border-slate-200 px-3 py-2"
          placeholder="Target roles (comma separated)"
          onChange={(e) =>
            setPayload((s) => ({ ...s, target_roles: e.target.value.split(",").map((v) => v.trim()).filter(Boolean) }))
          }
        />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <input
          className="rounded-lg border border-slate-200 px-3 py-2"
          placeholder="Target locations (comma separated)"
          onChange={(e) =>
            setPayload((s) => ({
              ...s,
              target_locations: e.target.value.split(",").map((v) => v.trim()).filter(Boolean)
            }))
          }
        />
        <input
          className="rounded-lg border border-slate-200 px-3 py-2"
          placeholder="Exclusions (comma separated)"
          onChange={(e) =>
            setPayload((s) => ({ ...s, exclusions: e.target.value.split(",").map((v) => v.trim()).filter(Boolean) }))
          }
        />
      </div>
      <button className="btn-primary" disabled={busy}>
        {busy ? "Creating..." : "Create Campaign"}
      </button>
    </form>
  );
}
