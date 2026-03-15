"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { ErrorState } from "@/components/ui/ErrorState";
import { api } from "@/services/api";

type BuilderAction = {
  key: string;
  name: string;
  description: string;
  default_status: string;
};

type WorkerTemplate = {
  id: string;
  workspace_id?: string | null;
  template_key: string;
  display_name: string;
  worker_type: string;
  worker_category: string;
  plan_version: string;
  is_public: boolean;
  is_active: boolean;
};

const INTERNAL_BUILDER_ENABLED = process.env.NEXT_PUBLIC_INTERNAL_WORKER_BUILDER_ENABLED === "true";

export default function InternalWorkerBuilderPage() {
  const router = useRouter();
  const [actions, setActions] = useState<BuilderAction[]>([]);
  const [templates, setTemplates] = useState<WorkerTemplate[]>([]);
  const [builderToken, setBuilderToken] = useState("");
  const [selectedActions, setSelectedActions] = useState<string[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [templateName, setTemplateName] = useState("Custom SDR Worker");
  const [workerName, setWorkerName] = useState("Custom Worker Alpha");
  const [workerMission, setWorkerMission] = useState("Drive qualified meetings this month.");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const actionMap = useMemo(() => new Map(actions.map((item) => [item.key, item])), [actions]);

  const headers = useMemo(
    () => (builderToken ? { "X-Internal-Builder-Token": builderToken } : undefined),
    [builderToken]
  );

  if (!INTERNAL_BUILDER_ENABLED) {
    return (
      <div className="space-y-4">
        <h2 className="section-title">Internal Worker Builder</h2>
        <div className="card border-amber-200/50 bg-amber-950/20 p-4 text-sm text-amber-200">
          Internal Worker Builder is disabled. Set <code>NEXT_PUBLIC_INTERNAL_WORKER_BUILDER_ENABLED=true</code> to
          access this route.
        </div>
      </div>
    );
  }

  const loadBuilderData = async () => {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const [actionData, templateData] = await Promise.all([
        api.get<BuilderAction[]>("/workers/internal/builder/actions", { headers }),
        api.get<WorkerTemplate[]>("/workers/internal/templates", { headers })
      ]);
      setActions(actionData);
      setTemplates(templateData);
      setSelectedActions((current) => current.filter((key) => actionData.some((item) => item.key === key)));
      if (!selectedTemplateId && templateData.length > 0) {
        setSelectedTemplateId(templateData[0].id);
      }
      setMessage("Internal builder data loaded.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load internal builder data");
    } finally {
      setBusy(false);
    }
  };

  const createTemplate = async () => {
    if (!templateName.trim()) {
      setError("Template name is required.");
      return;
    }
    if (!selectedActions.length) {
      setError("Select at least one action for the template.");
      return;
    }
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const steps = selectedActions.map((actionKey, index) => ({
        key: `step_${index + 1}_${actionKey}`,
        action_key: actionKey,
        status: actionMap.get(actionKey)?.default_status ?? "monitoring"
      }));
      const created = await api.post<WorkerTemplate>(
        "/workers/internal/templates",
        {
          display_name: templateName,
          worker_type: "custom_worker",
          worker_category: "custom",
          plan_version: "custom_v1",
          prompt_profile: "sales",
          allowed_actions: selectedActions,
          steps,
          config_defaults: {},
          mission_default: workerMission
        },
        { headers }
      );
      setSelectedTemplateId(created.id);
      await loadBuilderData();
      setMessage(`Created template "${created.display_name}".`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create template");
    } finally {
      setBusy(false);
    }
  };

  const createWorkerFromTemplate = async () => {
    if (!selectedTemplateId) {
      setError("Select a template first.");
      return;
    }
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const worker = await api.post<{ id: string }>(
        "/workers/internal/workers/from-template",
        {
          template_id: selectedTemplateId,
          name: workerName,
          mission: workerMission,
          tone: "professional",
          daily_send_limit: 40,
          run_interval_minutes: 60,
          config_overrides: {}
        },
        { headers }
      );
      setMessage("Internal custom worker created.");
      router.push(`/app/workers/${worker.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create worker from template");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="section-title">Internal Worker Builder</h2>
        <Link className="text-sm text-brand-600 hover:underline" href="/app/settings">
          Back to Settings
        </Link>
      </div>
      <div className="card border-amber-200/50 bg-amber-950/20 p-4 text-sm text-amber-200">
        Internal-only tooling. Do not share this route externally.
      </div>
      {error ? <ErrorState message={error} /> : null}
      {message ? <div className="card border-emerald-200/50 bg-emerald-950/20 p-4 text-sm text-emerald-200">{message}</div> : null}

      <div className="card space-y-3 p-4">
        <h3 className="text-base font-semibold">Internal Access</h3>
        <input
          className="w-full rounded-lg border border-slate-200 px-3 py-2"
          placeholder="Internal builder token (optional)"
          value={builderToken}
          onChange={(e) => setBuilderToken(e.target.value)}
        />
        <button className="btn-secondary" disabled={busy} onClick={loadBuilderData}>
          {busy ? "Loading..." : "Load Internal Builder Data"}
        </button>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card space-y-3 p-4">
          <h3 className="text-base font-semibold">Create Internal Template</h3>
          <input
            className="w-full rounded-lg border border-slate-200 px-3 py-2"
            placeholder="Template display name"
            value={templateName}
            onChange={(e) => setTemplateName(e.target.value)}
          />
          <p className="text-xs text-slate-500">Allowed actions</p>
          <div className="max-h-60 space-y-2 overflow-auto rounded-lg border border-slate-200 p-3">
            {actions.length === 0 ? (
              <p className="text-sm text-slate-500">Load builder data to view action catalog.</p>
            ) : (
              actions.map((action) => (
                <label className="flex items-start gap-2 text-sm" key={action.key}>
                  <input
                    type="checkbox"
                    checked={selectedActions.includes(action.key)}
                    onChange={(e) =>
                      setSelectedActions((current) =>
                        e.target.checked ? [...current, action.key] : current.filter((item) => item !== action.key)
                      )
                    }
                  />
                  <span>
                    <span className="font-medium">{action.name}</span>
                    <span className="block text-xs text-slate-500">{action.description}</span>
                  </span>
                </label>
              ))
            )}
          </div>
          <button className="btn-primary" disabled={busy} onClick={createTemplate}>
            Create Internal Template
          </button>
        </div>

        <div className="card space-y-3 p-4">
          <h3 className="text-base font-semibold">Create Worker From Template</h3>
          <select
            className="w-full rounded-lg border border-slate-200 px-3 py-2"
            value={selectedTemplateId}
            onChange={(e) => setSelectedTemplateId(e.target.value)}
          >
            <option value="">Select template</option>
            {templates.map((template) => (
              <option key={template.id} value={template.id}>
                {template.display_name} ({template.worker_type})
              </option>
            ))}
          </select>
          <input
            className="w-full rounded-lg border border-slate-200 px-3 py-2"
            placeholder="Worker name"
            value={workerName}
            onChange={(e) => setWorkerName(e.target.value)}
          />
          <textarea
            className="w-full rounded-lg border border-slate-200 px-3 py-2"
            placeholder="Mission"
            value={workerMission}
            onChange={(e) => setWorkerMission(e.target.value)}
          />
          <button className="btn-primary" disabled={busy} onClick={createWorkerFromTemplate}>
            Create Internal Worker
          </button>
        </div>
      </div>
    </div>
  );
}
