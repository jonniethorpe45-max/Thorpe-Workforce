"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/services/api";
import type {
  WorkerDraftCreateResponse,
  WorkerDraftListResponse,
  WorkerDraftPublishResponse,
  WorkerDraftRead,
  WorkerDraftTestResponse,
  WorkerInstanceRead
} from "@/types";

type DraftCategory =
  | "real_estate"
  | "marketing"
  | "finance"
  | "sales"
  | "ecommerce"
  | "content"
  | "research"
  | "automation"
  | "custom";

type DraftFormState = {
  name: string;
  slug: string;
  description: string;
  category: DraftCategory;
  promptTemplate: string;
  inputSchemaJson: string;
  outputSchemaJson: string;
  webSearch: boolean;
  databaseLookup: boolean;
  fileAccess: boolean;
  apiCall: boolean;
  visibility: "private" | "workspace" | "public" | "marketplace";
  priceMonthly: string;
  priceOnetime: string;
  tagsCsv: string;
  revenueCreator: string;
  revenuePlatform: string;
};

const defaultForm: DraftFormState = {
  name: "",
  slug: "",
  description: "",
  category: "custom",
  promptTemplate: "",
  inputSchemaJson: "{\n  \"type\": \"object\",\n  \"properties\": {}\n}",
  outputSchemaJson: "{\n  \"type\": \"object\",\n  \"properties\": {}\n}",
  webSearch: true,
  databaseLookup: false,
  fileAccess: false,
  apiCall: false,
  visibility: "private",
  priceMonthly: "",
  priceOnetime: "",
  tagsCsv: "",
  revenueCreator: "70",
  revenuePlatform: "30"
};

function parseJsonObject(value: string, field: string): Record<string, unknown> | null {
  if (!value.trim()) return null;
  try {
    const parsed = JSON.parse(value);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new Error(`${field} must be a JSON object`);
    }
    return parsed as Record<string, unknown>;
  } catch (error) {
    throw new Error(error instanceof Error ? `${field}: ${error.message}` : `${field} is invalid JSON`);
  }
}

function splitCsv(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function toForm(draft: WorkerDraftRead): DraftFormState {
  const tools = draft.tools_json ?? [];
  const enabled = (label: string) => tools.some((tool) => tool.label === label && tool.enabled);
  return {
    name: draft.name,
    slug: draft.slug,
    description: draft.description ?? "",
    category: (draft.category as DraftCategory) ?? "custom",
    promptTemplate: draft.prompt_template,
    inputSchemaJson: JSON.stringify(draft.input_schema_json ?? {}, null, 2),
    outputSchemaJson: JSON.stringify(draft.output_schema_json ?? {}, null, 2),
    webSearch: enabled("web_search"),
    databaseLookup: enabled("database_lookup"),
    fileAccess: enabled("file_access"),
    apiCall: enabled("api_call"),
    visibility: draft.visibility,
    priceMonthly: draft.price_monthly ? String(draft.price_monthly) : "",
    priceOnetime: draft.price_onetime ? String(draft.price_onetime) : "",
    tagsCsv: (draft.tags_json ?? []).join(", "),
    revenueCreator: String(draft.creator_revenue_percent ?? 70),
    revenuePlatform: String(draft.platform_revenue_percent ?? 30)
  };
}

export default function WorkerBuilderPage() {
  const [drafts, setDrafts] = useState<WorkerDraftRead[] | null>(null);
  const [selectedDraftId, setSelectedDraftId] = useState<string | null>(null);
  const [form, setForm] = useState<DraftFormState>(defaultForm);
  const [testInput, setTestInput] = useState("{\n  \"goal\": \"Generate one outreach idea\"\n}");
  const [testResult, setTestResult] = useState<WorkerDraftTestResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const selectedDraft = useMemo(() => drafts?.find((item) => item.id === selectedDraftId) ?? null, [drafts, selectedDraftId]);

  const load = useCallback(async () => {
    setError("");
    const data = await api.get<WorkerDraftListResponse>("/workers/builder/drafts");
    setDrafts(data.items);
  }, []);

  useEffect(() => {
    load().catch((err) => {
      const text = err instanceof Error ? err.message : "Failed to load worker creator";
      if (text.toLowerCase().includes("404")) {
        setError("Worker Creator is disabled. Set WORKER_CREATOR_ENABLED=true in backend environment.");
        return;
      }
      setError(text);
    });
  }, [load]);

  const resetForCreate = () => {
    setSelectedDraftId(null);
    setForm(defaultForm);
    setTestResult(null);
    setMessage("");
    setError("");
  };

  const selectDraft = (draft: WorkerDraftRead) => {
    setSelectedDraftId(draft.id);
    setForm(toForm(draft));
    setTestResult(null);
    setMessage("");
    setError("");
  };

  const payloadFromForm = () => ({
    name: form.name,
    slug: form.slug.trim() || null,
    description: form.description.trim() || null,
    category: form.category,
    prompt_template: form.promptTemplate,
    input_schema: parseJsonObject(form.inputSchemaJson, "input_schema"),
    output_schema: parseJsonObject(form.outputSchemaJson, "output_schema"),
    tools: [
      { label: "web_search", enabled: form.webSearch },
      { label: "database_lookup", enabled: form.databaseLookup },
      { label: "file_access", enabled: form.fileAccess },
      { label: "api_call", enabled: form.apiCall }
    ],
    visibility: form.visibility,
    price_monthly: form.priceMonthly ? Number(form.priceMonthly) : null,
    price_onetime: form.priceOnetime ? Number(form.priceOnetime) : null,
    tags: splitCsv(form.tagsCsv),
    creator_revenue_percent: Number(form.revenueCreator),
    platform_revenue_percent: Number(form.revenuePlatform)
  });

  const saveDraft = async () => {
    try {
      setBusy(true);
      setError("");
      const payload = payloadFromForm();
      if (selectedDraftId) {
        const updated = await api.patch<WorkerDraftRead>(`/workers/builder/drafts/${selectedDraftId}`, payload);
        setMessage(`Updated draft "${updated.name}".`);
        await load();
        setSelectedDraftId(updated.id);
        setForm(toForm(updated));
      } else {
        const created = await api.post<WorkerDraftCreateResponse>("/workers/builder/drafts", payload);
        setMessage(`Created draft "${created.draft.name}".`);
        await load();
        setSelectedDraftId(created.draft.id);
        setForm(toForm(created.draft));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save draft");
    } finally {
      setBusy(false);
    }
  };

  const testDraft = async () => {
    if (!selectedDraftId) {
      setError("Save the draft before running test.");
      return;
    }
    try {
      setBusy(true);
      setError("");
      const inputs = parseJsonObject(testInput, "inputs") ?? {};
      const result = await api.post<WorkerDraftTestResponse>(`/workers/builder/drafts/${selectedDraftId}/test`, { inputs });
      setTestResult(result);
      setMessage(`Test run ${result.run_id} completed with status ${result.status}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to test draft");
    } finally {
      setBusy(false);
    }
  };

  const publishDraft = async () => {
    if (!selectedDraftId) return;
    try {
      setBusy(true);
      setError("");
      const published = await api.post<WorkerDraftPublishResponse>(`/workers/builder/drafts/${selectedDraftId}/publish`, {});
      setMessage(`Published template "${published.template.display_name}".`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to publish draft");
    } finally {
      setBusy(false);
    }
  };

  const unpublishDraft = async () => {
    if (!selectedDraftId) return;
    try {
      setBusy(true);
      setError("");
      await api.post<WorkerDraftPublishResponse>(`/workers/builder/drafts/${selectedDraftId}/unpublish`, {});
      setMessage("Draft unpublished.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to unpublish draft");
    } finally {
      setBusy(false);
    }
  };

  const installDraft = async () => {
    if (!selectedDraftId) return;
    try {
      setBusy(true);
      setError("");
      const instance = await api.post<WorkerInstanceRead>(`/workers/builder/drafts/${selectedDraftId}/install`, {
        instance_name: `${form.name} Worker`,
        runtime_config_overrides: {},
        memory_scope: "instance"
      });
      setMessage(`Installed worker instance "${instance.name}".`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to install draft");
    } finally {
      setBusy(false);
    }
  };

  if (error && !drafts) return <ErrorState message={error} />;
  if (!drafts) return <LoadingState label="Loading worker creator..." />;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-2xl font-semibold">Worker Creator</h2>
          <p className="text-sm text-slate-600">Create, test, publish, and install custom AI workers.</p>
        </div>
        <div className="flex gap-2">
          <button className="btn-secondary" onClick={resetForCreate}>New Draft</button>
          <button className="btn-secondary" onClick={() => load().catch(() => undefined)}>Refresh</button>
        </div>
      </div>

      {error ? <ErrorState message={error} /> : null}
      {message ? <div className="card border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</div> : null}

      <div className="grid gap-4 xl:grid-cols-[1.1fr_1.9fr]">
        <div className="card overflow-hidden">
          <div className="border-b border-slate-200 px-4 py-3">
            <h3 className="text-base font-semibold">Drafts ({drafts.length})</h3>
          </div>
          {drafts.length === 0 ? (
            <div className="p-4">
              <EmptyState title="No drafts yet" description="Create a worker draft to begin." />
            </div>
          ) : (
            <div className="max-h-[640px] overflow-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-slate-100 text-left text-slate-600">
                  <tr>
                    <th className="px-4 py-2">Name</th>
                    <th className="px-4 py-2">Category</th>
                    <th className="px-4 py-2">Publish</th>
                    <th className="px-4 py-2" />
                  </tr>
                </thead>
                <tbody>
                  {drafts.map((draft) => (
                    <tr key={draft.id} className="border-t border-slate-200">
                      <td className="px-4 py-2">
                        <p className="font-medium text-slate-900">{draft.name}</p>
                        <p className="text-xs text-slate-500">{draft.slug}</p>
                      </td>
                      <td className="px-4 py-2 text-xs text-slate-600">{draft.category}</td>
                      <td className="px-4 py-2"><StatusBadge status={draft.is_published ? "active" : "draft"} /></td>
                      <td className="px-4 py-2 text-right">
                        <button className="text-xs font-medium text-brand-600 hover:underline" onClick={() => selectDraft(draft)}>Edit</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="card p-4">
          <h3 className="mb-4 text-base font-semibold">{selectedDraftId ? "Edit Worker Draft" : "Create Worker Draft"}</h3>

          <div className="grid gap-3 md:grid-cols-2">
            <label className="text-sm"><span className="mb-1 block text-slate-600">Name</span><input className="w-full rounded-lg border border-slate-200 px-3 py-2" value={form.name} onChange={(e) => setForm((c) => ({ ...c, name: e.target.value }))} /></label>
            <label className="text-sm"><span className="mb-1 block text-slate-600">Slug</span><input className="w-full rounded-lg border border-slate-200 px-3 py-2" value={form.slug} onChange={(e) => setForm((c) => ({ ...c, slug: e.target.value }))} /></label>
            <label className="text-sm"><span className="mb-1 block text-slate-600">Category</span><select className="w-full rounded-lg border border-slate-200 px-3 py-2" value={form.category} onChange={(e) => setForm((c) => ({ ...c, category: e.target.value as DraftCategory }))}><option value="custom">custom</option><option value="sales">sales</option><option value="real_estate">real_estate</option><option value="marketing">marketing</option><option value="finance">finance</option><option value="ecommerce">ecommerce</option><option value="content">content</option><option value="research">research</option><option value="automation">automation</option></select></label>
            <label className="text-sm"><span className="mb-1 block text-slate-600">Visibility</span><select className="w-full rounded-lg border border-slate-200 px-3 py-2" value={form.visibility} onChange={(e) => setForm((c) => ({ ...c, visibility: e.target.value as DraftFormState["visibility"] }))}><option value="private">private</option><option value="workspace">workspace</option><option value="public">public</option><option value="marketplace">marketplace</option></select></label>
            <label className="text-sm"><span className="mb-1 block text-slate-600">Price Monthly (USD)</span><input type="number" min={0} step="0.01" className="w-full rounded-lg border border-slate-200 px-3 py-2" value={form.priceMonthly} onChange={(e) => setForm((c) => ({ ...c, priceMonthly: e.target.value }))} /></label>
            <label className="text-sm"><span className="mb-1 block text-slate-600">Price One-time (USD)</span><input type="number" min={0} step="0.01" className="w-full rounded-lg border border-slate-200 px-3 py-2" value={form.priceOnetime} onChange={(e) => setForm((c) => ({ ...c, priceOnetime: e.target.value }))} /></label>
            <label className="text-sm"><span className="mb-1 block text-slate-600">Creator Revenue %</span><input type="number" min={0} max={100} step="0.1" className="w-full rounded-lg border border-slate-200 px-3 py-2" value={form.revenueCreator} onChange={(e) => setForm((c) => ({ ...c, revenueCreator: e.target.value }))} /></label>
            <label className="text-sm"><span className="mb-1 block text-slate-600">Platform Revenue %</span><input type="number" min={0} max={100} step="0.1" className="w-full rounded-lg border border-slate-200 px-3 py-2" value={form.revenuePlatform} onChange={(e) => setForm((c) => ({ ...c, revenuePlatform: e.target.value }))} /></label>
            <label className="text-sm md:col-span-2"><span className="mb-1 block text-slate-600">Description</span><textarea className="h-20 w-full rounded-lg border border-slate-200 px-3 py-2" value={form.description} onChange={(e) => setForm((c) => ({ ...c, description: e.target.value }))} /></label>
            <label className="text-sm md:col-span-2"><span className="mb-1 block text-slate-600">Prompt Template</span><textarea className="h-28 w-full rounded-lg border border-slate-200 px-3 py-2" value={form.promptTemplate} onChange={(e) => setForm((c) => ({ ...c, promptTemplate: e.target.value }))} /></label>
            <label className="text-sm md:col-span-2"><span className="mb-1 block text-slate-600">Input Schema JSON</span><textarea className="h-24 w-full rounded-lg border border-slate-200 px-3 py-2 font-mono text-xs" value={form.inputSchemaJson} onChange={(e) => setForm((c) => ({ ...c, inputSchemaJson: e.target.value }))} /></label>
            <label className="text-sm md:col-span-2"><span className="mb-1 block text-slate-600">Output Schema JSON</span><textarea className="h-24 w-full rounded-lg border border-slate-200 px-3 py-2 font-mono text-xs" value={form.outputSchemaJson} onChange={(e) => setForm((c) => ({ ...c, outputSchemaJson: e.target.value }))} /></label>
            <label className="text-sm md:col-span-2"><span className="mb-1 block text-slate-600">Tags (comma-separated)</span><input className="w-full rounded-lg border border-slate-200 px-3 py-2" value={form.tagsCsv} onChange={(e) => setForm((c) => ({ ...c, tagsCsv: e.target.value }))} /></label>
            <div className="text-sm md:col-span-2">
              <span className="mb-1 block text-slate-600">Tools</span>
              <div className="grid gap-2 rounded-lg border border-slate-200 p-3 sm:grid-cols-2">
                <label className="inline-flex items-center gap-2 text-xs"><input type="checkbox" checked={form.webSearch} onChange={(e) => setForm((c) => ({ ...c, webSearch: e.target.checked }))} />web_search</label>
                <label className="inline-flex items-center gap-2 text-xs"><input type="checkbox" checked={form.databaseLookup} onChange={(e) => setForm((c) => ({ ...c, databaseLookup: e.target.checked }))} />database_lookup</label>
                <label className="inline-flex items-center gap-2 text-xs"><input type="checkbox" checked={form.fileAccess} onChange={(e) => setForm((c) => ({ ...c, fileAccess: e.target.checked }))} />file_access</label>
                <label className="inline-flex items-center gap-2 text-xs"><input type="checkbox" checked={form.apiCall} onChange={(e) => setForm((c) => ({ ...c, apiCall: e.target.checked }))} />api_call</label>
              </div>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <button className="btn-primary" disabled={busy} onClick={saveDraft}>{busy ? "Saving..." : selectedDraftId ? "Save Draft" : "Create Draft"}</button>
            <button className="btn-secondary" disabled={busy || !selectedDraftId} onClick={testDraft}>Run Test</button>
            <button className="btn-secondary" disabled={busy || !selectedDraftId} onClick={publishDraft}>Publish</button>
            <button className="btn-secondary" disabled={busy || !selectedDraft?.is_published} onClick={installDraft}>Install</button>
            <button className="btn-secondary" disabled={busy || !selectedDraft?.is_published} onClick={unpublishDraft}>Unpublish</button>
          </div>

          <div className="mt-4 rounded-lg border border-slate-200 p-3">
            <p className="mb-2 text-sm font-medium text-slate-800">Test Inputs (JSON)</p>
            <textarea className="h-24 w-full rounded-lg border border-slate-200 px-3 py-2 font-mono text-xs" value={testInput} onChange={(e) => setTestInput(e.target.value)} />
            {testResult ? (
              <div className="mt-3 text-xs">
                <p><span className="font-medium">Run:</span> {testResult.run_id}</p>
                <p><span className="font-medium">Status:</span> {testResult.status}</p>
                <pre className="mt-2 overflow-auto rounded bg-slate-950 p-2 text-slate-100">{JSON.stringify(testResult.normalized_output, null, 2)}</pre>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
