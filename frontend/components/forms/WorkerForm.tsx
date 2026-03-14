"use client";

import { FormEvent, useState } from "react";

type Payload = {
  name: string;
  goal: string;
  target_industry: string;
  target_roles: string[];
  target_locations: string[];
  company_size_range: string;
  tone: string;
  daily_send_limit: number;
  run_interval_minutes: number;
};

export function WorkerForm({ onSubmit }: { onSubmit: (payload: Payload) => Promise<void> }) {
  const [payload, setPayload] = useState<Payload>({
    name: "AI Sales Worker",
    goal: "",
    target_industry: "",
    target_roles: [],
    target_locations: [],
    company_size_range: "",
    tone: "professional",
    daily_send_limit: 40,
    run_interval_minutes: 60
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
      <h2 className="text-lg font-semibold">Create AI Sales Worker</h2>
      <input
        className="w-full rounded-lg border border-slate-200 px-3 py-2"
        placeholder="Worker name"
        value={payload.name}
        onChange={(e) => setPayload((s) => ({ ...s, name: e.target.value }))}
        required
      />
      <textarea
        className="w-full rounded-lg border border-slate-200 px-3 py-2"
        placeholder="Goal"
        value={payload.goal}
        onChange={(e) => setPayload((s) => ({ ...s, goal: e.target.value }))}
        required
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
          placeholder="Company size range (e.g. 50-500)"
          value={payload.company_size_range}
          onChange={(e) => setPayload((s) => ({ ...s, company_size_range: e.target.value }))}
        />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <input
          className="rounded-lg border border-slate-200 px-3 py-2"
          placeholder="Target roles (comma separated)"
          onChange={(e) =>
            setPayload((s) => ({ ...s, target_roles: e.target.value.split(",").map((v) => v.trim()).filter(Boolean) }))
          }
        />
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
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <select
          className="rounded-lg border border-slate-200 px-3 py-2"
          value={payload.tone}
          onChange={(e) => setPayload((s) => ({ ...s, tone: e.target.value }))}
        >
          <option value="professional">Professional</option>
          <option value="concise">Concise</option>
          <option value="friendly">Friendly</option>
        </select>
        <input
          type="number"
          className="rounded-lg border border-slate-200 px-3 py-2"
          min={1}
          max={500}
          value={payload.daily_send_limit}
          onChange={(e) => setPayload((s) => ({ ...s, daily_send_limit: Number(e.target.value) }))}
        />
      </div>
      <input
        type="number"
        className="w-full rounded-lg border border-slate-200 px-3 py-2"
        min={15}
        max={1440}
        value={payload.run_interval_minutes}
        onChange={(e) => setPayload((s) => ({ ...s, run_interval_minutes: Number(e.target.value) }))}
        placeholder="Run interval in minutes"
      />
      <button className="btn-primary" disabled={busy}>
        {busy ? "Creating..." : "Create Worker"}
      </button>
    </form>
  );
}
