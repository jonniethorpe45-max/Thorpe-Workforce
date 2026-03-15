"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/services/api";
import type {
  WorkerChainListResponse,
  WorkerChainRead,
  WorkerChainRunResponse,
  WorkerInstanceRead,
  WorkerTemplateRead
} from "@/types";

type StepDraft = {
  step_order: number;
  step_name: string;
  worker_instance_id: string;
  worker_template_id: string;
  input_mapping_json: string;
  condition_json: string;
  on_success_next_step: string;
  on_failure_next_step: string;
};

type ChainForm = {
  name: string;
  description: string;
  status: "draft" | "active" | "paused" | "archived";
  trigger_type: "manual" | "schedule" | "event" | "api";
  trigger_config_json: string;
  steps: StepDraft[];
};

const defaultForm: ChainForm = {
  name: "",
  description: "",
  status: "draft",
  trigger_type: "manual",
  trigger_config_json: "{}",
  steps: [
    {
      step_order: 1,
      step_name: "",
      worker_instance_id: "",
      worker_template_id: "",
      input_mapping_json: "{}",
      condition_json: "{}",
      on_success_next_step: "",
      on_failure_next_step: ""
    }
  ]
};

function parseJsonObject(value: string, field: string): Record<string, unknown> {
  try {
    const parsed = JSON.parse(value || "{}");
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new Error(`${field} must be a JSON object`);
    }
    return parsed as Record<string, unknown>;
  } catch (error) {
    throw new Error(error instanceof Error ? `${field}: ${error.message}` : `${field} is invalid JSON`);
  }
}

function parseOptionalJsonObject(value: string, field: string): Record<string, unknown> | null {
  const cleaned = value.trim();
  if (!cleaned) return null;
  if (cleaned === "{}") return null;
  return parseJsonObject(cleaned, field);
}

function toForm(chain: WorkerChainRead): ChainForm {
  const steps = [...chain.steps]
    .sort((a, b) => a.step_order - b.step_order)
    .map((step) => ({
      step_order: step.step_order,
      step_name: step.step_name,
      worker_instance_id: step.worker_instance_id ?? "",
      worker_template_id: step.worker_template_id ?? "",
      input_mapping_json: JSON.stringify(step.input_mapping_json ?? {}, null, 2),
      condition_json: step.condition_json ? JSON.stringify(step.condition_json, null, 2) : "{}",
      on_success_next_step: step.on_success_next_step ? String(step.on_success_next_step) : "",
      on_failure_next_step: step.on_failure_next_step ? String(step.on_failure_next_step) : ""
    }));
  return {
    name: chain.name,
    description: chain.description ?? "",
    status: chain.status,
    trigger_type: chain.trigger_type,
    trigger_config_json: JSON.stringify(chain.trigger_config_json ?? {}, null, 2),
    steps: steps.length ? steps : defaultForm.steps
  };
}

export default function WorkerChainsPage() {
  const [chains, setChains] = useState<WorkerChainRead[] | null>(null);
  const [instances, setInstances] = useState<WorkerInstanceRead[]>([]);
  const [templates, setTemplates] = useState<WorkerTemplateRead[]>([]);
  const [selectedChainId, setSelectedChainId] = useState<string | null>(null);
  const [form, setForm] = useState<ChainForm>(defaultForm);
  const [runInput, setRunInput] = useState("{\n  \"seed\": \"manual\"\n}");
  const [latestRun, setLatestRun] = useState<WorkerChainRunResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const selectedChain = useMemo(() => chains?.find((item) => item.id === selectedChainId) ?? null, [chains, selectedChainId]);

  const load = useCallback(async () => {
    setError("");
    const [chainResponse, instanceData, templateData] = await Promise.all([
      api.get<WorkerChainListResponse>("/worker-chains"),
      api.get<WorkerInstanceRead[]>("/workers/instances"),
      api.get<WorkerTemplateRead[]>("/workers/templates?include_public=true")
    ]);
    setChains(chainResponse.items);
    setInstances(instanceData);
    setTemplates(templateData);
  }, []);

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load worker chains"));
  }, [load]);

  const setStep = (index: number, next: Partial<StepDraft>) => {
    setForm((current) => ({
      ...current,
      steps: current.steps.map((item, stepIndex) => (stepIndex === index ? { ...item, ...next } : item))
    }));
  };

  const addStep = () => {
    setForm((current) => {
      const maxOrder = current.steps.reduce((max, step) => Math.max(max, step.step_order), 0);
      return {
        ...current,
        steps: [
          ...current.steps,
          {
            step_order: maxOrder + 1,
            step_name: "",
            worker_instance_id: "",
            worker_template_id: "",
            input_mapping_json: "{}",
            condition_json: "{}",
            on_success_next_step: "",
            on_failure_next_step: ""
          }
        ]
      };
    });
  };

  const removeStep = (index: number) => {
    setForm((current) => {
      if (current.steps.length <= 1) return current;
      return { ...current, steps: current.steps.filter((_, stepIndex) => stepIndex !== index) };
    });
  };

  const saveChain = async () => {
    try {
      setBusy(true);
      setError("");
      setMessage("");
      const payload = {
        name: form.name,
        description: form.description || null,
        status: form.status,
        trigger_type: form.trigger_type,
        trigger_config_json: parseJsonObject(form.trigger_config_json, "trigger_config_json"),
        steps: form.steps.map((step) => ({
          step_order: Number(step.step_order),
          step_name: step.step_name,
          worker_instance_id: step.worker_instance_id || null,
          worker_template_id: step.worker_template_id || null,
          input_mapping_json: parseJsonObject(step.input_mapping_json, `step ${step.step_order} input_mapping_json`),
          condition_json: parseOptionalJsonObject(step.condition_json, `step ${step.step_order} condition_json`),
          on_success_next_step: step.on_success_next_step ? Number(step.on_success_next_step) : null,
          on_failure_next_step: step.on_failure_next_step ? Number(step.on_failure_next_step) : null
        }))
      };
      if (selectedChainId) {
        const updated = await api.patch<WorkerChainRead>(`/worker-chains/${selectedChainId}`, payload);
        setMessage(`Updated chain "${updated.name}".`);
        await load();
      } else {
        const created = await api.post<WorkerChainRead>("/worker-chains", payload);
        setMessage(`Created chain "${created.name}".`);
        await load();
        setSelectedChainId(created.id);
        setForm(toForm(created));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save worker chain");
    } finally {
      setBusy(false);
    }
  };

  const runSelectedChain = async () => {
    if (!selectedChainId) {
      setError("Select a chain before running.");
      return;
    }
    try {
      setBusy(true);
      setError("");
      const payload = { runtime_input: parseJsonObject(runInput, "runtime_input") };
      const response = await api.post<WorkerChainRunResponse>(`/worker-chains/${selectedChainId}/run`, payload);
      setLatestRun(response);
      setMessage(`Chain run ${response.status}. Executed ${response.total_steps_executed} step(s).`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run chain");
    } finally {
      setBusy(false);
    }
  };

  const selectChain = (chain: WorkerChainRead) => {
    setSelectedChainId(chain.id);
    setForm(toForm(chain));
    setLatestRun(null);
    setMessage("");
    setError("");
  };

  const startNewChain = () => {
    setSelectedChainId(null);
    setForm(defaultForm);
    setLatestRun(null);
    setMessage("");
    setError("");
  };

  if (error && !chains) return <ErrorState message={error} />;
  if (!chains) return <LoadingState label="Loading worker chains..." />;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="section-title">Worker Chains</h2>
          <p className="text-sm text-slate-600">Compose multi-step worker flows and run them manually.</p>
        </div>
        <div className="flex gap-2">
          <button className="btn-secondary" onClick={startNewChain}>
            New Chain
          </button>
          <button className="btn-secondary" onClick={() => load().catch(() => undefined)}>
            Refresh
          </button>
        </div>
      </div>
      {error ? <ErrorState message={error} /> : null}
      {message ? <div className="card border-emerald-200/50 bg-emerald-950/20 p-3 text-sm text-emerald-200">{message}</div> : null}

      <div className="grid gap-4 xl:grid-cols-[1.1fr_1.9fr]">
        <div className="card p-4">
          <h3 className="text-base font-semibold">Existing Chains ({chains.length})</h3>
          <div className="mt-3 space-y-2">
            {!chains.length ? (
              <EmptyState title="No chains yet" description="Create your first chain using templates or installed instances." />
            ) : (
              chains.map((chain) => (
                <button
                  className="w-full rounded-lg border border-slate-200/70 bg-slate-900/40 p-3 text-left hover:bg-slate-900/75"
                  key={chain.id}
                  onClick={() => selectChain(chain)}
                  type="button"
                >
                  <div className="flex items-center justify-between">
                    <p className="font-medium">{chain.name}</p>
                    <StatusBadge status={chain.status} />
                  </div>
                  <p className="text-xs text-slate-500">
                    Trigger: {chain.trigger_type} • Steps: {chain.steps.length}
                  </p>
                  {chain.steps.length ? (
                    <ol className="mt-2 list-inside list-decimal text-xs text-slate-600">
                      {[...chain.steps]
                        .sort((a, b) => a.step_order - b.step_order)
                        .slice(0, 4)
                        .map((step) => (
                          <li key={step.id}>
                            {step.step_order}. {step.step_name}
                          </li>
                        ))}
                    </ol>
                  ) : null}
                </button>
              ))
            )}
          </div>
        </div>

        <div className="card p-4">
          <h3 className="mb-3 text-base font-semibold">{selectedChain ? `Edit Chain: ${selectedChain.name}` : "Create Chain"}</h3>
          <div className="grid gap-3 md:grid-cols-2">
            <label className="text-sm">
              <span className="mb-1 block text-slate-600">Name</span>
              <input
                className="w-full rounded-lg border border-slate-200 px-3 py-2"
                value={form.name}
                onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
              />
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-slate-600">Status</span>
              <select
                className="w-full rounded-lg border border-slate-200 px-3 py-2"
                value={form.status}
                onChange={(event) => setForm((current) => ({ ...current, status: event.target.value as ChainForm["status"] }))}
              >
                <option value="draft">draft</option>
                <option value="active">active</option>
                <option value="paused">paused</option>
                <option value="archived">archived</option>
              </select>
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-slate-600">Trigger Type</span>
              <select
                className="w-full rounded-lg border border-slate-200 px-3 py-2"
                value={form.trigger_type}
                onChange={(event) => setForm((current) => ({ ...current, trigger_type: event.target.value as ChainForm["trigger_type"] }))}
              >
                <option value="manual">manual</option>
                <option value="api">api</option>
                <option value="schedule">schedule</option>
                <option value="event">event</option>
              </select>
            </label>
            <label className="text-sm md:col-span-2">
              <span className="mb-1 block text-slate-600">Description</span>
              <textarea
                className="h-20 w-full rounded-lg border border-slate-200 px-3 py-2"
                value={form.description}
                onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
              />
            </label>
            <label className="text-sm md:col-span-2">
              <span className="mb-1 block text-slate-600">Trigger Config JSON</span>
              <textarea
                className="h-20 w-full rounded-lg border border-slate-200 px-3 py-2 font-mono text-xs"
                value={form.trigger_config_json}
                onChange={(event) => setForm((current) => ({ ...current, trigger_config_json: event.target.value }))}
              />
            </label>
          </div>

          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold">Ordered Steps</h4>
              <button className="btn-secondary px-3 py-1 text-xs" onClick={addStep} type="button">
                Add Step
              </button>
            </div>
            {form.steps.map((step, index) => (
              <div className="rounded-lg border border-slate-200/70 bg-slate-900/35 p-3" key={`${step.step_order}-${index}`}>
                <div className="grid gap-2 md:grid-cols-3">
                  <label className="text-xs">
                    <span className="mb-1 block text-slate-600">Step Order</span>
                    <input
                      className="w-full rounded border border-slate-200 px-2 py-1"
                      min={1}
                      onChange={(event) => setStep(index, { step_order: Number(event.target.value || 1) })}
                      type="number"
                      value={step.step_order}
                    />
                  </label>
                  <label className="text-xs md:col-span-2">
                    <span className="mb-1 block text-slate-600">Step Name</span>
                    <input
                      className="w-full rounded border border-slate-200 px-2 py-1"
                      onChange={(event) => setStep(index, { step_name: event.target.value })}
                      value={step.step_name}
                    />
                  </label>
                  <label className="text-xs">
                    <span className="mb-1 block text-slate-600">Worker Instance</span>
                    <select
                      className="w-full rounded border border-slate-200 px-2 py-1"
                      onChange={(event) =>
                        setStep(index, {
                          worker_instance_id: event.target.value,
                          worker_template_id: event.target.value ? "" : step.worker_template_id
                        })
                      }
                      value={step.worker_instance_id}
                    >
                      <option value="">Select instance</option>
                      {instances.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="text-xs">
                    <span className="mb-1 block text-slate-600">Worker Template</span>
                    <select
                      className="w-full rounded border border-slate-200 px-2 py-1"
                      onChange={(event) =>
                        setStep(index, {
                          worker_template_id: event.target.value,
                          worker_instance_id: event.target.value ? "" : step.worker_instance_id
                        })
                      }
                      value={step.worker_template_id}
                    >
                      <option value="">Select template</option>
                      {templates.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.display_name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="text-xs">
                    <span className="mb-1 block text-slate-600">On Success Next</span>
                    <input
                      className="w-full rounded border border-slate-200 px-2 py-1"
                      onChange={(event) => setStep(index, { on_success_next_step: event.target.value })}
                      placeholder="auto"
                      type="number"
                      value={step.on_success_next_step}
                    />
                  </label>
                  <label className="text-xs">
                    <span className="mb-1 block text-slate-600">On Failure Next</span>
                    <input
                      className="w-full rounded border border-slate-200 px-2 py-1"
                      onChange={(event) => setStep(index, { on_failure_next_step: event.target.value })}
                      placeholder="stop"
                      type="number"
                      value={step.on_failure_next_step}
                    />
                  </label>
                  <label className="text-xs md:col-span-2">
                    <span className="mb-1 block text-slate-600">Input Mapping JSON</span>
                    <textarea
                      className="h-16 w-full rounded border border-slate-200 px-2 py-1 font-mono"
                      onChange={(event) => setStep(index, { input_mapping_json: event.target.value })}
                      value={step.input_mapping_json}
                    />
                  </label>
                  <label className="text-xs md:col-span-3">
                    <span className="mb-1 block text-slate-600">Condition JSON (placeholder for future logic)</span>
                    <textarea
                      className="h-14 w-full rounded border border-slate-200 px-2 py-1 font-mono"
                      onChange={(event) => setStep(index, { condition_json: event.target.value })}
                      value={step.condition_json}
                    />
                  </label>
                </div>
                <div className="mt-2 text-right">
                  <button className="text-xs text-rose-600 hover:underline" onClick={() => removeStep(index)} type="button">
                    Remove step
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <button className="btn-primary" disabled={busy} onClick={saveChain}>
              {busy ? "Saving..." : selectedChain ? "Save Chain" : "Create Chain"}
            </button>
            <button className="btn-secondary" disabled={busy || !selectedChainId} onClick={runSelectedChain}>
              {busy ? "Running..." : "Run Chain Manually"}
            </button>
          </div>

          <div className="mt-3">
            <label className="text-sm">
              <span className="mb-1 block text-slate-600">Manual Run Input JSON</span>
              <textarea
                className="h-20 w-full rounded-lg border border-slate-200 px-3 py-2 font-mono text-xs"
                onChange={(event) => setRunInput(event.target.value)}
                value={runInput}
              />
            </label>
          </div>

          {latestRun ? (
            <div className="mt-4 rounded-lg border border-slate-200/70 bg-slate-900/35 p-3">
              <div className="flex items-center justify-between">
                <p className="font-medium">Latest Chain Run</p>
                <StatusBadge status={latestRun.status} />
              </div>
              <p className="text-xs text-slate-500">
                Chain run ID: {latestRun.chain_run_id} • Steps executed: {latestRun.total_steps_executed}
              </p>
              <ol className="mt-2 list-inside list-decimal space-y-1 text-sm text-slate-700">
                {latestRun.executed_steps.map((step) => (
                  <li key={`${latestRun.chain_run_id}-${step.step_order}`}>
                    Step {step.step_order}: {step.status}
                    {step.error ? ` (${step.error})` : ""}
                  </li>
                ))}
              </ol>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
