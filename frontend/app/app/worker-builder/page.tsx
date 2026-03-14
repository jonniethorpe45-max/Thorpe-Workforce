"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/services/api";
import type { WorkerTemplateRead, WorkerToolListResponse, WorkerToolRead } from "@/types";

type TemplateFormState = {
  name: string;
  slug: string;
  shortDescription: string;
  description: string;
  category: string;
  workerType: string;
  workerCategory: string;
  visibility: "private" | "workspace" | "public" | "marketplace";
  status: "draft" | "active" | "archived";
  instructions: string;
  modelName: string;
  configJson: string;
  capabilitiesJson: string;
  actionsCsv: string;
  selectedTools: string[];
  memoryEnabled: boolean;
  chainEnabled: boolean;
  isMarketplaceListed: boolean;
  pricingType: "free" | "subscription" | "one_time" | "internal";
  priceCents: number;
  currency: string;
  tagsCsv: string;
};

const defaultForm: TemplateFormState = {
  name: "",
  slug: "",
  shortDescription: "",
  description: "",
  category: "general",
  workerType: "custom_worker",
  workerCategory: "general",
  visibility: "workspace",
  status: "draft",
  instructions: "",
  modelName: "mock-ai-v1",
  configJson: "{\n  \"mission\": \"\"\n}",
  capabilitiesJson: "{}",
  actionsCsv: "",
  selectedTools: [],
  memoryEnabled: true,
  chainEnabled: false,
  isMarketplaceListed: false,
  pricingType: "internal",
  priceCents: 0,
  currency: "USD",
  tagsCsv: ""
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

function splitCsv(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function centsToLabel(priceCents: number, currency: string, pricingType: string): string {
  if (pricingType === "free") return "Free";
  if (pricingType === "internal") return "Internal";
  return `${(priceCents / 100).toFixed(2)} ${currency.toUpperCase()}`;
}

function toForm(template: WorkerTemplateRead): TemplateFormState {
  return {
    name: template.name,
    slug: template.slug ?? "",
    shortDescription: template.short_description ?? "",
    description: template.description ?? "",
    category: template.category,
    workerType: template.worker_type,
    workerCategory: template.worker_category,
    visibility: template.visibility,
    status: template.status,
    instructions: template.instructions ?? "",
    modelName: template.model_name ?? "mock-ai-v1",
    configJson: JSON.stringify(template.config_json ?? {}, null, 2),
    capabilitiesJson: JSON.stringify(template.capabilities_json ?? {}, null, 2),
    actionsCsv: (template.actions_json ?? []).join(", "),
    selectedTools: template.tools_json ?? [],
    memoryEnabled: template.memory_enabled,
    chainEnabled: template.chain_enabled,
    isMarketplaceListed: template.is_marketplace_listed,
    pricingType: template.pricing_type,
    priceCents: template.price_cents,
    currency: template.currency,
    tagsCsv: (template.tags_json ?? []).join(", ")
  };
}

export default function WorkerBuilderPage() {
  const [templates, setTemplates] = useState<WorkerTemplateRead[] | null>(null);
  const [tools, setTools] = useState<WorkerToolRead[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [form, setForm] = useState<TemplateFormState>(defaultForm);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const selectedTemplate = useMemo(
    () => templates?.find((item) => item.id === selectedTemplateId) ?? null,
    [templates, selectedTemplateId]
  );
  const isEditMode = Boolean(selectedTemplateId);
  const canEditTemplate = Boolean(selectedTemplate?.workspace_id);

  const load = useCallback(async () => {
    setError("");
    const [templateData, toolData] = await Promise.all([
      api.get<WorkerTemplateRead[]>("/workers/templates?include_public=true"),
      api.get<WorkerToolListResponse>("/worker-tools")
    ]);
    setTemplates(templateData);
    setTools(toolData.items);
  }, []);

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load worker builder data"));
  }, [load]);

  const resetForCreate = () => {
    setSelectedTemplateId(null);
    setForm(defaultForm);
    setMessage("");
    setError("");
  };

  const selectTemplate = (template: WorkerTemplateRead) => {
    setSelectedTemplateId(template.id);
    setForm(toForm(template));
    setError("");
    setMessage("");
  };

  const saveTemplate = async () => {
    try {
      setBusy(true);
      setError("");
      setMessage("");
      const payload = {
        name: form.name,
        slug: form.slug.trim() || null,
        short_description: form.shortDescription.trim() || null,
        description: form.description.trim() || null,
        category: form.category.trim(),
        worker_type: form.workerType.trim(),
        worker_category: form.workerCategory.trim(),
        visibility: form.visibility,
        status: form.status,
        instructions: form.instructions.trim() || null,
        model_name: form.modelName.trim() || null,
        config_json: parseJsonObject(form.configJson, "config_json"),
        capabilities_json: parseJsonObject(form.capabilitiesJson, "capabilities_json"),
        actions_json: splitCsv(form.actionsCsv),
        tools_json: form.selectedTools,
        memory_enabled: form.memoryEnabled,
        chain_enabled: form.chainEnabled,
        is_marketplace_listed: form.isMarketplaceListed,
        pricing_type: form.pricingType,
        price_cents: Number(form.priceCents || 0),
        currency: form.currency.trim().toUpperCase(),
        tags_json: splitCsv(form.tagsCsv)
      };

      if (selectedTemplateId) {
        if (!canEditTemplate) {
          throw new Error("This template is read-only. Duplicate it into your workspace before editing.");
        }
        const updated = await api.patch<WorkerTemplateRead>(`/workers/templates/${selectedTemplateId}`, payload);
        setMessage(`Updated template "${updated.display_name}".`);
        await load();
        setSelectedTemplateId(updated.id);
        setForm(toForm(updated));
      } else {
        const created = await api.post<WorkerTemplateRead>("/workers/templates", payload);
        setMessage(`Created template "${created.display_name}".`);
        await load();
        setSelectedTemplateId(created.id);
        setForm(toForm(created));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save template");
    } finally {
      setBusy(false);
    }
  };

  const publishTemplate = async () => {
    if (!selectedTemplateId) {
      setError("Select a template to publish.");
      return;
    }
    if (!canEditTemplate) {
      setError("Only workspace templates can be published from this screen.");
      return;
    }
    try {
      setBusy(true);
      setError("");
      setMessage("");
      const payload = {
        name: form.name,
        slug: form.slug,
        description: form.description,
        instructions: form.instructions,
        model_name: form.modelName,
        config_json: parseJsonObject(form.configJson, "config_json"),
        visibility: form.visibility,
        is_marketplace_listed: form.isMarketplaceListed,
        pricing_type: form.pricingType,
        price_cents: Number(form.priceCents || 0),
        currency: form.currency.trim().toUpperCase()
      };
      const published = await api.post<WorkerTemplateRead>(`/workers/templates/${selectedTemplateId}/publish`, payload);
      setMessage(`Published "${published.display_name}" as ${published.visibility}.`);
      await load();
      setSelectedTemplateId(published.id);
      setForm(toForm(published));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to publish template");
    } finally {
      setBusy(false);
    }
  };

  const toggleTool = (slug: string) => {
    setForm((current) => ({
      ...current,
      selectedTools: current.selectedTools.includes(slug)
        ? current.selectedTools.filter((item) => item !== slug)
        : [...current.selectedTools, slug]
    }));
  };

  if (error && !templates) return <ErrorState message={error} />;
  if (!templates) return <LoadingState label="Loading worker builder..." />;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-2xl font-semibold">Worker Builder</h2>
          <p className="text-sm text-slate-600">Create, edit, and publish worker templates for your workspace.</p>
        </div>
        <div className="flex gap-2">
          <button className="btn-secondary" onClick={resetForCreate}>
            New Template
          </button>
          <button className="btn-secondary" onClick={() => load().catch(() => undefined)}>
            Refresh
          </button>
        </div>
      </div>

      {error ? <ErrorState message={error} /> : null}
      {message ? <div className="card border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</div> : null}

      <div className="grid gap-4 xl:grid-cols-[1.2fr_1.8fr]">
        <div className="card overflow-hidden">
          <div className="border-b border-slate-200 px-4 py-3">
            <h3 className="text-base font-semibold">Template Library ({templates.length})</h3>
          </div>
          {templates.length === 0 ? (
            <div className="p-4">
              <EmptyState title="No templates yet" description="Create your first worker template to start building." />
            </div>
          ) : (
            <div className="max-h-[640px] overflow-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-slate-100 text-left text-slate-600">
                  <tr>
                    <th className="px-4 py-2">Template</th>
                    <th className="px-4 py-2">Visibility</th>
                    <th className="px-4 py-2">Status</th>
                    <th className="px-4 py-2">Pricing</th>
                    <th className="px-4 py-2" />
                  </tr>
                </thead>
                <tbody>
                  {templates.map((template) => (
                    <tr key={template.id} className="border-t border-slate-200">
                      <td className="px-4 py-2">
                        <p className="font-medium text-slate-900">{template.display_name}</p>
                        <p className="text-xs text-slate-500">
                          {template.worker_type} • {template.slug || "no-slug"}
                        </p>
                      </td>
                      <td className="px-4 py-2 text-xs text-slate-600">{template.visibility}</td>
                      <td className="px-4 py-2">
                        <StatusBadge status={template.status} />
                      </td>
                      <td className="px-4 py-2 text-xs text-slate-600">
                        {centsToLabel(template.price_cents, template.currency, template.pricing_type)}
                      </td>
                      <td className="px-4 py-2 text-right">
                        <button className="text-xs font-medium text-brand-600 hover:underline" onClick={() => selectTemplate(template)}>
                          Edit
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="card p-4">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-base font-semibold">{isEditMode ? "Edit Template" : "Create Template"}</h3>
            {selectedTemplate && !canEditTemplate ? (
              <span className="rounded-full bg-amber-50 px-2 py-1 text-xs font-medium text-amber-700">Read-only public template</span>
            ) : null}
          </div>

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
              <span className="mb-1 block text-slate-600">Slug</span>
              <input
                className="w-full rounded-lg border border-slate-200 px-3 py-2"
                value={form.slug}
                onChange={(event) => setForm((current) => ({ ...current, slug: event.target.value }))}
              />
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-slate-600">Category</span>
              <input
                className="w-full rounded-lg border border-slate-200 px-3 py-2"
                value={form.category}
                onChange={(event) => setForm((current) => ({ ...current, category: event.target.value }))}
              />
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-slate-600">Worker Type</span>
              <input
                className="w-full rounded-lg border border-slate-200 px-3 py-2"
                value={form.workerType}
                onChange={(event) => setForm((current) => ({ ...current, workerType: event.target.value }))}
              />
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-slate-600">Worker Category</span>
              <input
                className="w-full rounded-lg border border-slate-200 px-3 py-2"
                value={form.workerCategory}
                onChange={(event) => setForm((current) => ({ ...current, workerCategory: event.target.value }))}
              />
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-slate-600">Model</span>
              <input
                className="w-full rounded-lg border border-slate-200 px-3 py-2"
                value={form.modelName}
                onChange={(event) => setForm((current) => ({ ...current, modelName: event.target.value }))}
              />
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-slate-600">Visibility</span>
              <select
                className="w-full rounded-lg border border-slate-200 px-3 py-2"
                value={form.visibility}
                onChange={(event) =>
                  setForm((current) => ({ ...current, visibility: event.target.value as TemplateFormState["visibility"] }))
                }
              >
                <option value="workspace">workspace</option>
                <option value="public">public</option>
                <option value="marketplace">marketplace</option>
                <option value="private">private</option>
              </select>
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-slate-600">Status</span>
              <select
                className="w-full rounded-lg border border-slate-200 px-3 py-2"
                value={form.status}
                onChange={(event) => setForm((current) => ({ ...current, status: event.target.value as TemplateFormState["status"] }))}
              >
                <option value="draft">draft</option>
                <option value="active">active</option>
                <option value="archived">archived</option>
              </select>
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-slate-600">Pricing Type</span>
              <select
                className="w-full rounded-lg border border-slate-200 px-3 py-2"
                value={form.pricingType}
                onChange={(event) =>
                  setForm((current) => ({ ...current, pricingType: event.target.value as TemplateFormState["pricingType"] }))
                }
              >
                <option value="internal">internal</option>
                <option value="free">free</option>
                <option value="subscription">subscription</option>
                <option value="one_time">one_time</option>
              </select>
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-slate-600">Price (cents)</span>
              <input
                className="w-full rounded-lg border border-slate-200 px-3 py-2"
                type="number"
                min={0}
                value={form.priceCents}
                onChange={(event) => setForm((current) => ({ ...current, priceCents: Number(event.target.value || 0) }))}
              />
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-slate-600">Currency</span>
              <input
                className="w-full rounded-lg border border-slate-200 px-3 py-2"
                value={form.currency}
                onChange={(event) => setForm((current) => ({ ...current, currency: event.target.value.toUpperCase() }))}
              />
            </label>
            <label className="text-sm md:col-span-2">
              <span className="mb-1 block text-slate-600">Short Description</span>
              <input
                className="w-full rounded-lg border border-slate-200 px-3 py-2"
                value={form.shortDescription}
                onChange={(event) => setForm((current) => ({ ...current, shortDescription: event.target.value }))}
              />
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
              <span className="mb-1 block text-slate-600">Instructions</span>
              <textarea
                className="h-24 w-full rounded-lg border border-slate-200 px-3 py-2"
                value={form.instructions}
                onChange={(event) => setForm((current) => ({ ...current, instructions: event.target.value }))}
              />
            </label>
            <label className="text-sm md:col-span-2">
              <span className="mb-1 block text-slate-600">Actions (comma separated)</span>
              <input
                className="w-full rounded-lg border border-slate-200 px-3 py-2"
                value={form.actionsCsv}
                onChange={(event) => setForm((current) => ({ ...current, actionsCsv: event.target.value }))}
              />
            </label>
            <label className="text-sm md:col-span-2">
              <span className="mb-1 block text-slate-600">Tags (comma separated)</span>
              <input
                className="w-full rounded-lg border border-slate-200 px-3 py-2"
                value={form.tagsCsv}
                onChange={(event) => setForm((current) => ({ ...current, tagsCsv: event.target.value }))}
              />
            </label>
            <label className="text-sm md:col-span-2">
              <span className="mb-1 block text-slate-600">Config JSON</span>
              <textarea
                className="h-28 w-full rounded-lg border border-slate-200 px-3 py-2 font-mono text-xs"
                value={form.configJson}
                onChange={(event) => setForm((current) => ({ ...current, configJson: event.target.value }))}
              />
            </label>
            <label className="text-sm md:col-span-2">
              <span className="mb-1 block text-slate-600">Capabilities JSON</span>
              <textarea
                className="h-24 w-full rounded-lg border border-slate-200 px-3 py-2 font-mono text-xs"
                value={form.capabilitiesJson}
                onChange={(event) => setForm((current) => ({ ...current, capabilitiesJson: event.target.value }))}
              />
            </label>
            <div className="text-sm md:col-span-2">
              <span className="mb-2 block text-slate-600">Allowed Tools</span>
              <div className="grid gap-2 rounded-lg border border-slate-200 p-3 sm:grid-cols-2">
                {tools.map((tool) => (
                  <label className="flex items-start gap-2 text-xs text-slate-700" key={tool.id}>
                    <input
                      checked={form.selectedTools.includes(tool.slug)}
                      onChange={() => toggleTool(tool.slug)}
                      type="checkbox"
                    />
                    <span>
                      <span className="font-medium">{tool.name}</span>
                      <span className="block text-slate-500">{tool.slug}</span>
                    </span>
                  </label>
                ))}
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-4 text-sm md:col-span-2">
              <label className="inline-flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={form.memoryEnabled}
                  onChange={(event) => setForm((current) => ({ ...current, memoryEnabled: event.target.checked }))}
                />
                Memory enabled
              </label>
              <label className="inline-flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={form.chainEnabled}
                  onChange={(event) => setForm((current) => ({ ...current, chainEnabled: event.target.checked }))}
                />
                Chain enabled
              </label>
              <label className="inline-flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={form.isMarketplaceListed}
                  onChange={(event) => setForm((current) => ({ ...current, isMarketplaceListed: event.target.checked }))}
                />
                Marketplace listed
              </label>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <button className="btn-primary" disabled={busy || (isEditMode && !canEditTemplate)} onClick={saveTemplate}>
              {busy ? "Saving..." : isEditMode ? "Save Changes" : "Create Template"}
            </button>
            <button
              className="btn-secondary"
              disabled={busy || !isEditMode || !canEditTemplate}
              onClick={publishTemplate}
            >
              {busy ? "Publishing..." : "Publish Template"}
            </button>
          </div>
          <p className="mt-2 text-xs text-slate-500">
            Publish requires complete name/slug/description/instructions/model/config and valid pricing when listed.
          </p>
        </div>
      </div>
    </div>
  );
}
