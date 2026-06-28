import { useEffect, useState } from "react";
import {
  Bot,
  KeyRound,
  Shield,
  Activity,
  FileText,
  Settings2,
  RefreshCw,
  Plus,
  CheckCircle2,
  XCircle,
  AlertCircle,
} from "lucide-react";
import { thorpeApi } from "../services/tauri";
import { useAppStore } from "../services/store";
import type {
  AiAgentRecord,
  AiOrgPolicy,
  AiProviderRecord,
  EnterpriseAiDashboard,
} from "../services/types";

type Tab = "providers" | "agents" | "policy" | "usage" | "audit" | "health";

const ROLE_OPTIONS = ["admin", "technician", "user"];
const MODEL_OPTIONS = ["gpt-4o-mini", "gpt-4o", "claude-3-5-sonnet-latest", "claude-3-haiku-20240307"];

function HealthBadge({ status }: { status: string }) {
  if (status === "healthy") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-400">
        <CheckCircle2 className="h-3 w-3" /> Healthy
      </span>
    );
  }
  if (status === "unhealthy") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-500/15 px-2 py-0.5 text-xs text-red-400">
        <XCircle className="h-3 w-3" /> Unhealthy
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/15 px-2 py-0.5 text-xs text-amber-400">
      <AlertCircle className="h-3 w-3" /> Unknown
    </span>
  );
}

function RoleCheckboxes({
  roles,
  selected,
  onChange,
}: {
  roles: string[];
  selected: string[];
  onChange: (roles: string[]) => void;
}) {
  return (
    <div className="flex flex-wrap gap-3">
      {roles.map((role) => (
        <label key={role} className="flex items-center gap-2 text-sm text-gray-300">
          <input
            type="checkbox"
            checked={selected.includes(role)}
            onChange={(e) => {
              if (e.target.checked) onChange([...selected, role]);
              else onChange(selected.filter((r) => r !== role));
            }}
            className="rounded border-surface-border bg-surface-overlay text-thorpe-500"
          />
          <span className="capitalize">{role}</span>
        </label>
      ))}
    </div>
  );
}

export function EnterpriseAiConsole() {
  const [featureAllowed, setFeatureAllowed] = useState<boolean | null>(null);
  const [dashboard, setDashboard] = useState<EnterpriseAiDashboard | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("providers");
  const [loading, setLoading] = useState(false);
  const [providerKeyInputs, setProviderKeyInputs] = useState<Record<string, string>>({});
  const [newProvider, setNewProvider] = useState({
    name: "",
    provider_type: "openai",
    base_url: "https://api.openai.com/v1",
    enabled: true,
    api_key: "",
    allowed_roles: ["admin", "technician", "user"],
  });
  const { addNotification } = useAppStore();

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const data = await thorpeApi.getEnterpriseAiDashboard();
      setDashboard(data);
    } catch (err) {
      addNotification({ type: "error", title: "Load Failed", message: String(err) });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    thorpeApi.checkFeature("enterprise_ai_console").then((f) => {
      setFeatureAllowed(f.allowed);
      if (f.allowed) loadDashboard();
    });
  }, []);

  const saveProvider = async (provider: Partial<AiProviderRecord> & { api_key?: string }) => {
    try {
      await thorpeApi.upsertAiProvider({
        id: provider.id,
        name: provider.name!,
        provider_type: provider.provider_type!,
        base_url: provider.base_url!,
        enabled: provider.enabled ?? true,
        api_key: provider.api_key,
        allowed_roles: provider.allowed_roles ?? ["admin", "technician", "user"],
      });
      addNotification({ type: "success", title: "Provider Saved", message: `${provider.name} updated.` });
      await loadDashboard();
    } catch (err) {
      addNotification({ type: "error", title: "Save Failed", message: String(err) });
    }
  };

  const rotateKey = async (providerId: string, name: string) => {
    const key = providerKeyInputs[providerId]?.trim();
    if (!key) {
      addNotification({ type: "error", title: "API Key Required", message: "Enter a new API key to rotate." });
      return;
    }
    try {
      await thorpeApi.rotateProviderApiKey(providerId, key);
      setProviderKeyInputs((prev) => ({ ...prev, [providerId]: "" }));
      addNotification({
        type: "success",
        title: "Key Rotated",
        message: `API key for ${name} updated without redeploying.`,
      });
      await loadDashboard();
    } catch (err) {
      addNotification({ type: "error", title: "Rotation Failed", message: String(err) });
    }
  };

  const saveAgent = async (agent: AiAgentRecord) => {
    try {
      await thorpeApi.upsertAiAgent({
        agent_key: agent.agent_key,
        name: agent.name,
        provider_id: agent.provider_id,
        model: agent.model,
        enabled: agent.enabled,
        allowed_roles: agent.allowed_roles,
      });
      addNotification({ type: "success", title: "Agent Saved", message: `${agent.name} configuration updated.` });
      await loadDashboard();
    } catch (err) {
      addNotification({ type: "error", title: "Save Failed", message: String(err) });
    }
  };

  const savePolicy = async (policy: AiOrgPolicy) => {
    try {
      await thorpeApi.updateAiOrgPolicy({
        cloud_ai_enabled: policy.cloud_ai_enabled,
        default_provider_id: policy.default_provider_id,
        monthly_budget_usd: policy.monthly_budget_usd,
        monthly_token_limit: policy.monthly_token_limit,
        enforce_budget: policy.enforce_budget,
      });
      addNotification({ type: "success", title: "Policy Saved", message: "Organization AI policy updated." });
      await loadDashboard();
    } catch (err) {
      addNotification({ type: "error", title: "Save Failed", message: String(err) });
    }
  };

  const testHealth = async (providerId: string) => {
    try {
      const result = await thorpeApi.testAiProviderHealth(providerId);
      addNotification({
        type: result.status === "healthy" ? "success" : "error",
        title: "Health Check",
        message: result.message,
      });
      await loadDashboard();
    } catch (err) {
      addNotification({ type: "error", title: "Health Check Failed", message: String(err) });
    }
  };

  if (featureAllowed === false) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20 animate-fade-in">
        <Shield className="h-16 w-16 text-gray-600" />
        <h2 className="text-xl font-bold text-white">Enterprise AI Management Console</h2>
        <p className="max-w-md text-center text-gray-400">
          Securely manage API keys, models, budgets, and access controls for your organization&apos;s AI
          providers. Requires an Enterprise license.
        </p>
        <a href="/licensing" className="btn-primary">
          View Licensing
        </a>
      </div>
    );
  }

  if (featureAllowed === null || !dashboard) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-thorpe-500 border-t-transparent" />
      </div>
    );
  }

  const tabs: { id: Tab; label: string; icon: typeof Bot }[] = [
    { id: "providers", label: "Providers", icon: KeyRound },
    { id: "agents", label: "Agents", icon: Bot },
    { id: "policy", label: "Policy & Budgets", icon: Settings2 },
    { id: "usage", label: "Usage", icon: Activity },
    { id: "health", label: "Health", icon: RefreshCw },
    { id: "audit", label: "Audit Log", icon: FileText },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Enterprise AI Console</h1>
          <p className="mt-1 text-gray-400">
            Manage providers, models, budgets, and access — rotate keys without redeploying.
          </p>
        </div>
        <button onClick={loadDashboard} disabled={loading} className="btn-secondary flex items-center gap-2">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card p-4">
          <p className="text-xs uppercase tracking-wide text-gray-500">Monthly spend</p>
          <p className="mt-1 text-2xl font-bold text-white">
            ${dashboard.usage.estimated_cost_usd.toFixed(2)}
          </p>
          <p className="text-xs text-gray-400">
            {dashboard.usage.budget_used_percent.toFixed(0)}% of ${dashboard.policy.monthly_budget_usd} budget
          </p>
        </div>
        <div className="card p-4">
          <p className="text-xs uppercase tracking-wide text-gray-500">Tokens ({dashboard.usage.month})</p>
          <p className="mt-1 text-2xl font-bold text-white">
            {dashboard.usage.total_tokens.toLocaleString()}
          </p>
          <p className="text-xs text-gray-400">
            {dashboard.usage.token_limit_used_percent.toFixed(0)}% of limit
          </p>
        </div>
        <div className="card p-4">
          <p className="text-xs uppercase tracking-wide text-gray-500">Requests</p>
          <p className="mt-1 text-2xl font-bold text-white">{dashboard.usage.request_count}</p>
          <p className="text-xs text-gray-400">This month</p>
        </div>
        <div className="card p-4">
          <p className="text-xs uppercase tracking-wide text-gray-500">Cloud AI</p>
          <p className="mt-1 text-2xl font-bold text-white">
            {dashboard.policy.cloud_ai_enabled ? "Enabled" : "Disabled"}
          </p>
          <p className="text-xs text-gray-400">
            {dashboard.policy.enforce_budget ? "Budget enforced" : "Budget advisory"}
          </p>
        </div>
      </div>

      <div className="flex gap-2 overflow-x-auto border-b border-surface-border">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex shrink-0 items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              activeTab === id
                ? "border-thorpe-500 text-thorpe-400"
                : "border-transparent text-gray-400 hover:text-gray-200"
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {activeTab === "providers" && (
        <div className="space-y-6">
          {dashboard.providers.map((provider) => (
            <ProviderCard
              key={provider.id}
              provider={provider}
              roles={dashboard.roles}
              keyInput={providerKeyInputs[provider.id] ?? ""}
              onKeyInputChange={(v) => setProviderKeyInputs((prev) => ({ ...prev, [provider.id]: v }))}
              onSave={saveProvider}
              onRotateKey={() => rotateKey(provider.id, provider.name)}
            />
          ))}

          <div className="card space-y-4 p-5">
            <h3 className="flex items-center gap-2 font-semibold text-white">
              <Plus className="h-4 w-4" /> Add Provider
            </h3>
            <div className="grid gap-4 md:grid-cols-2">
              <input
                className="input"
                placeholder="Provider name"
                value={newProvider.name}
                onChange={(e) => setNewProvider({ ...newProvider, name: e.target.value })}
              />
              <select
                className="input"
                value={newProvider.provider_type}
                onChange={(e) =>
                  setNewProvider({
                    ...newProvider,
                    provider_type: e.target.value,
                    base_url:
                      e.target.value === "anthropic"
                        ? "https://api.anthropic.com/v1"
                        : "https://api.openai.com/v1",
                  })
                }
              >
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="custom">Custom (OpenAI-compatible)</option>
              </select>
              <input
                className="input md:col-span-2"
                placeholder="Base URL"
                value={newProvider.base_url}
                onChange={(e) => setNewProvider({ ...newProvider, base_url: e.target.value })}
              />
              <input
                className="input md:col-span-2"
                type="password"
                placeholder="API key"
                value={newProvider.api_key}
                onChange={(e) => setNewProvider({ ...newProvider, api_key: e.target.value })}
              />
            </div>
            <RoleCheckboxes
              roles={ROLE_OPTIONS}
              selected={newProvider.allowed_roles}
              onChange={(allowed_roles) => setNewProvider({ ...newProvider, allowed_roles })}
            />
            <button
              className="btn-primary"
              onClick={() => {
                if (!newProvider.name.trim()) return;
                saveProvider(newProvider).then(() =>
                  setNewProvider({
                    name: "",
                    provider_type: "openai",
                    base_url: "https://api.openai.com/v1",
                    enabled: true,
                    api_key: "",
                    allowed_roles: ["admin", "technician", "user"],
                  })
                );
              }}
            >
              Add Provider
            </button>
          </div>
        </div>
      )}

      {activeTab === "agents" && (
        <div className="space-y-4">
          {dashboard.agents.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              providers={dashboard.providers}
              roles={dashboard.roles}
              onSave={saveAgent}
            />
          ))}
        </div>
      )}

      {activeTab === "policy" && (
        <PolicyPanel policy={dashboard.policy} providers={dashboard.providers} onSave={savePolicy} />
      )}

      {activeTab === "usage" && (
        <div className="card p-5 space-y-4">
          <h3 className="font-semibold text-white">Usage — {dashboard.usage.month}</h3>
          <div className="grid gap-4 md:grid-cols-2">
            <UsageBar
              label="Budget"
              used={dashboard.usage.estimated_cost_usd}
              limit={dashboard.policy.monthly_budget_usd}
              unit="$"
            />
            <UsageBar
              label="Tokens"
              used={dashboard.usage.total_tokens}
              limit={dashboard.policy.monthly_token_limit}
            />
          </div>
          <dl className="grid gap-3 text-sm md:grid-cols-2">
            <div>
              <dt className="text-gray-500">Prompt tokens</dt>
              <dd className="text-white">{dashboard.usage.prompt_tokens.toLocaleString()}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Completion tokens</dt>
              <dd className="text-white">{dashboard.usage.completion_tokens.toLocaleString()}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Estimated cost</dt>
              <dd className="text-white">${dashboard.usage.estimated_cost_usd.toFixed(4)}</dd>
            </div>
            <div>
              <dt className="text-gray-500">API requests</dt>
              <dd className="text-white">{dashboard.usage.request_count}</dd>
            </div>
          </dl>
        </div>
      )}

      {activeTab === "health" && (
        <div className="space-y-3">
          {dashboard.providers.map((provider) => (
            <div key={provider.id} className="card flex items-center justify-between p-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-white">{provider.name}</span>
                  <HealthBadge status={provider.health_status} />
                </div>
                {provider.health_message && (
                  <p className="mt-1 text-sm text-gray-400">{provider.health_message}</p>
                )}
                {provider.last_health_check_at && (
                  <p className="mt-1 text-xs text-gray-500">
                    Last checked: {new Date(provider.last_health_check_at).toLocaleString()}
                  </p>
                )}
              </div>
              <button className="btn-secondary" onClick={() => testHealth(provider.id)}>
                Test Connection
              </button>
            </div>
          ))}
        </div>
      )}

      {activeTab === "audit" && (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="border-b border-surface-border bg-surface-overlay/50 text-left text-gray-400">
              <tr>
                <th className="px-4 py-3">Time</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Actor</th>
                <th className="px-4 py-3">Details</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.audit_log.map((entry) => (
                <tr key={entry.id} className="border-b border-surface-border/50">
                  <td className="px-4 py-3 text-gray-400">
                    {new Date(entry.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-thorpe-400">{entry.action}</td>
                  <td className="px-4 py-3 text-white">{entry.actor}</td>
                  <td className="px-4 py-3 text-gray-300">{entry.details}</td>
                </tr>
              ))}
              {dashboard.audit_log.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                    No audit events yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function ProviderCard({
  provider,
  roles,
  keyInput,
  onKeyInputChange,
  onSave,
  onRotateKey,
}: {
  provider: AiProviderRecord;
  roles: string[];
  keyInput: string;
  onKeyInputChange: (v: string) => void;
  onSave: (p: Partial<AiProviderRecord> & { api_key?: string }) => Promise<void>;
  onRotateKey: () => void;
}) {
  const [draft, setDraft] = useState(provider);

  useEffect(() => setDraft(provider), [provider]);

  return (
    <div className="card space-y-4 p-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h3 className="font-semibold text-white">{draft.name}</h3>
          <HealthBadge status={draft.health_status} />
          {draft.api_key_configured ? (
            <span className="text-xs text-emerald-400">Key configured</span>
          ) : (
            <span className="text-xs text-amber-400">No key</span>
          )}
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-300">
          <input
            type="checkbox"
            checked={draft.enabled}
            onChange={(e) => setDraft({ ...draft, enabled: e.target.checked })}
          />
          Enabled
        </label>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <input
          className="input"
          value={draft.name}
          onChange={(e) => setDraft({ ...draft, name: e.target.value })}
        />
        <input
          className="input"
          value={draft.base_url}
          onChange={(e) => setDraft({ ...draft, base_url: e.target.value })}
        />
      </div>
      <div>
        <p className="mb-2 text-sm text-gray-400">Role access</p>
        <RoleCheckboxes
          roles={roles}
          selected={draft.allowed_roles}
          onChange={(allowed_roles) => setDraft({ ...draft, allowed_roles })}
        />
      </div>
      <div className="flex flex-col gap-2 sm:flex-row">
        <input
          className="input flex-1"
          type="password"
          placeholder="Rotate API key (stored in OS keychain)"
          value={keyInput}
          onChange={(e) => onKeyInputChange(e.target.value)}
        />
        <button className="btn-secondary" onClick={onRotateKey}>
          Rotate Key
        </button>
      </div>
      <button className="btn-primary" onClick={() => onSave(draft)}>
        Save Provider
      </button>
    </div>
  );
}

function AgentCard({
  agent,
  providers,
  roles,
  onSave,
}: {
  agent: AiAgentRecord;
  providers: AiProviderRecord[];
  roles: string[];
  onSave: (a: AiAgentRecord) => Promise<void>;
}) {
  const [draft, setDraft] = useState(agent);

  useEffect(() => setDraft(agent), [agent]);

  return (
    <div className="card space-y-4 p-5">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-white">{draft.name}</h3>
        <label className="flex items-center gap-2 text-sm text-gray-300">
          <input
            type="checkbox"
            checked={draft.enabled}
            onChange={(e) => setDraft({ ...draft, enabled: e.target.checked })}
          />
          Enabled
        </label>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <select
          className="input"
          value={draft.provider_id ?? ""}
          onChange={(e) =>
            setDraft({ ...draft, provider_id: e.target.value || null })
          }
        >
          <option value="">Use global default</option>
          {providers.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <select
          className="input"
          value={draft.model}
          onChange={(e) => setDraft({ ...draft, model: e.target.value })}
        >
          {MODEL_OPTIONS.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </div>
      <div>
        <p className="mb-2 text-sm text-gray-400">Allowed roles</p>
        <RoleCheckboxes
          roles={roles}
          selected={draft.allowed_roles}
          onChange={(allowed_roles) => setDraft({ ...draft, allowed_roles })}
        />
      </div>
      <button className="btn-primary" onClick={() => onSave(draft)}>
        Save Agent
      </button>
    </div>
  );
}

function PolicyPanel({
  policy,
  providers,
  onSave,
}: {
  policy: AiOrgPolicy;
  providers: AiProviderRecord[];
  onSave: (p: AiOrgPolicy) => Promise<void>;
}) {
  const [draft, setDraft] = useState(policy);

  useEffect(() => setDraft(policy), [policy]);

  return (
    <div className="card space-y-4 p-5">
      <h3 className="font-semibold text-white">Organization Policy</h3>
      <label className="flex items-center gap-2 text-sm text-gray-300">
        <input
          type="checkbox"
          checked={draft.cloud_ai_enabled}
          onChange={(e) => setDraft({ ...draft, cloud_ai_enabled: e.target.checked })}
        />
        Enable Cloud AI organization-wide
      </label>
      <label className="flex items-center gap-2 text-sm text-gray-300">
        <input
          type="checkbox"
          checked={draft.enforce_budget}
          onChange={(e) => setDraft({ ...draft, enforce_budget: e.target.checked })}
        />
        Enforce monthly budget and token limits
      </label>
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <label className="mb-1 block text-sm text-gray-400">Default provider</label>
          <select
            className="input"
            value={draft.default_provider_id ?? ""}
            onChange={(e) =>
              setDraft({ ...draft, default_provider_id: e.target.value || null })
            }
          >
            <option value="">None</option>
            {providers.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm text-gray-400">Monthly budget (USD)</label>
          <input
            className="input"
            type="number"
            min={0}
            step={1}
            value={draft.monthly_budget_usd}
            onChange={(e) =>
              setDraft({ ...draft, monthly_budget_usd: parseFloat(e.target.value) || 0 })
            }
          />
        </div>
        <div>
          <label className="mb-1 block text-sm text-gray-400">Monthly token limit</label>
          <input
            className="input"
            type="number"
            min={0}
            step={1000}
            value={draft.monthly_token_limit}
            onChange={(e) =>
              setDraft({ ...draft, monthly_token_limit: parseInt(e.target.value, 10) || 0 })
            }
          />
        </div>
      </div>
      <button className="btn-primary" onClick={() => onSave(draft)}>
        Save Policy
      </button>
    </div>
  );
}

function UsageBar({
  label,
  used,
  limit,
  unit = "",
}: {
  label: string;
  used: number;
  limit: number;
  unit?: string;
}) {
  const pct = limit > 0 ? Math.min((used / limit) * 100, 100) : 0;
  const color = pct >= 90 ? "bg-red-500" : pct >= 70 ? "bg-amber-500" : "bg-thorpe-500";

  return (
    <div>
      <div className="mb-1 flex justify-between text-sm">
        <span className="text-gray-400">{label}</span>
        <span className="text-white">
          {unit}
          {used.toLocaleString(undefined, { maximumFractionDigits: 2 })} / {unit}
          {limit.toLocaleString()}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-surface-overlay">
        <div className={`h-full ${color} transition-all`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
