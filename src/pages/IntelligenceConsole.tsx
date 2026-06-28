import { useEffect, useState } from "react";
import {
  Brain,
  BookMarked,
  Package,
  History,
  RefreshCw,
  Plus,
  Download,
  AlertTriangle,
} from "lucide-react";
import { thorpeApi } from "../services/tauri";
import { useAppStore } from "../services/store";
import type {
  AgentPlan,
  AgentSessionRecord,
  IntelItem,
  OrgPlaybook,
  RepairPackRecord,
} from "../services/types";

type Tab = "intel" | "playbooks" | "packs" | "sessions";

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: "bg-red-500/15 text-red-400",
    high: "bg-orange-500/15 text-orange-400",
    medium: "bg-amber-500/15 text-amber-400",
    info: "bg-cyan-500/15 text-cyan-400",
  };
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs capitalize ${colors[severity] ?? "bg-gray-500/15 text-gray-400"}`}
    >
      {severity}
    </span>
  );
}

function parsePlan(json: string): AgentPlan | null {
  try {
    return JSON.parse(json) as AgentPlan;
  } catch {
    return null;
  }
}

export function IntelligenceConsole() {
  const [featureAllowed, setFeatureAllowed] = useState<boolean | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("intel");
  const [loading, setLoading] = useState(false);
  const [intelItems, setIntelItems] = useState<IntelItem[]>([]);
  const [playbooks, setPlaybooks] = useState<OrgPlaybook[]>([]);
  const [packs, setPacks] = useState<RepairPackRecord[]>([]);
  const [sessions, setSessions] = useState<AgentSessionRecord[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [newPlaybook, setNewPlaybook] = useState({
    title: "",
    category: "General",
    content: "",
    tags: "",
  });
  const { addNotification } = useAppStore();

  const loadAll = async () => {
    setLoading(true);
    try {
      const [intel, pb, pk, sess] = await Promise.all([
        thorpeApi.listIntelItems(50),
        thorpeApi.listOrgPlaybooks(),
        thorpeApi.listRepairPacks(),
        thorpeApi.listAgentSessions(50),
      ]);
      setIntelItems(intel);
      setPlaybooks(pb);
      setPacks(pk);
      setSessions(sess);
    } catch (err) {
      addNotification({ type: "error", title: "Load Failed", message: String(err) });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    thorpeApi.checkFeature("intelligence_console").then((f) => {
      setFeatureAllowed(f.allowed);
      if (f.allowed) loadAll();
    });
  }, []);

  const syncIntel = async () => {
    setSyncing(true);
    try {
      const count = await thorpeApi.syncIntelFeed();
      addNotification({
        type: "success",
        title: "Intel synced",
        message: `${count} item(s) imported from feed.`,
      });
      const intel = await thorpeApi.listIntelItems(50);
      setIntelItems(intel);
    } catch (err) {
      addNotification({ type: "error", title: "Sync Failed", message: String(err) });
    } finally {
      setSyncing(false);
    }
  };

  const savePlaybook = async () => {
    if (!newPlaybook.title.trim() || !newPlaybook.content.trim()) return;
    try {
      await thorpeApi.upsertOrgPlaybook(
        newPlaybook.title,
        newPlaybook.category,
        newPlaybook.content,
        newPlaybook.tags.split(",").map((t) => t.trim()).filter(Boolean)
      );
      setNewPlaybook({ title: "", category: "General", content: "", tags: "" });
      const pb = await thorpeApi.listOrgPlaybooks();
      setPlaybooks(pb);
      addNotification({ type: "success", title: "Playbook saved", message: "Org playbook added." });
    } catch (err) {
      addNotification({ type: "error", title: "Save Failed", message: String(err) });
    }
  };

  if (featureAllowed === null) {
    return <div className="animate-pulse text-steel">Checking license…</div>;
  }

  if (!featureAllowed) {
    return (
      <div className="card mx-auto max-w-lg p-8 text-center">
        <Brain className="mx-auto mb-4 h-12 w-12 text-steel" />
        <h1 className="text-xl font-bold text-white">Intelligence Console</h1>
        <p className="mt-2 text-sm text-steel">
          Requires an Enterprise license. Activate your license on the Licensing page to access
          threat intel, org playbooks, repair packs, and agent session history.
        </p>
      </div>
    );
  }

  const tabs: { id: Tab; label: string; icon: typeof Brain }[] = [
    { id: "intel", label: "Threat Intel", icon: AlertTriangle },
    { id: "playbooks", label: "Playbooks", icon: BookMarked },
    { id: "packs", label: "Repair Packs", icon: Package },
    { id: "sessions", label: "Agent Sessions", icon: History },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-thorpe-primary">
            Senior Engineer Platform
          </p>
          <h1 className="text-2xl font-bold text-white">Intelligence Console</h1>
          <p className="mt-1 text-sm text-steel">
            RAG intel feed, org playbooks, signed repair packs, and Jonathan agent sessions.
          </p>
        </div>
        <button onClick={loadAll} disabled={loading} className="btn-secondary text-sm">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      <div className="flex flex-wrap gap-2 border-b border-navy-border pb-2">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === id
                ? "bg-thorpe-primary/20 text-thorpe-primary"
                : "text-steel hover:bg-surface-overlay hover:text-slate-200"
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {activeTab === "intel" && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button onClick={syncIntel} disabled={syncing} className="btn-primary text-sm">
              <Download className={`h-4 w-4 ${syncing ? "animate-pulse" : ""}`} />
              Sync intel feed
            </button>
          </div>
          <div className="grid gap-3">
            {intelItems.map((item) => (
              <div key={item.id} className="card p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <SeverityBadge severity={item.severity} />
                      <span className="text-xs text-steel">{item.category}</span>
                    </div>
                    <h3 className="mt-1 font-medium text-white">{item.title}</h3>
                    <p className="mt-1 text-sm text-steel">{item.summary}</p>
                    {item.url && (
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noreferrer"
                        className="mt-2 inline-block text-xs text-thorpe-primary hover:underline"
                      >
                        Source: {item.source}
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {intelItems.length === 0 && (
              <p className="text-center text-sm text-steel">No intel items yet. Sync the feed to import.</p>
            )}
          </div>
        </div>
      )}

      {activeTab === "playbooks" && (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="card space-y-3 p-4">
            <h2 className="flex items-center gap-2 font-medium text-white">
              <Plus className="h-4 w-4" /> New playbook
            </h2>
            <input
              className="input"
              placeholder="Title"
              value={newPlaybook.title}
              onChange={(e) => setNewPlaybook({ ...newPlaybook, title: e.target.value })}
            />
            <input
              className="input"
              placeholder="Category"
              value={newPlaybook.category}
              onChange={(e) => setNewPlaybook({ ...newPlaybook, category: e.target.value })}
            />
            <textarea
              className="input min-h-[120px]"
              placeholder="Playbook content (steps, runbooks…)"
              value={newPlaybook.content}
              onChange={(e) => setNewPlaybook({ ...newPlaybook, content: e.target.value })}
            />
            <input
              className="input"
              placeholder="Tags (comma-separated)"
              value={newPlaybook.tags}
              onChange={(e) => setNewPlaybook({ ...newPlaybook, tags: e.target.value })}
            />
            <button onClick={savePlaybook} className="btn-primary text-sm">
              Save playbook
            </button>
          </div>
          <div className="space-y-3">
            {playbooks.map((pb) => (
              <div key={pb.id} className="card p-4">
                <h3 className="font-medium text-white">{pb.title}</h3>
                <p className="text-xs text-steel">{pb.category}</p>
                <p className="mt-2 whitespace-pre-wrap text-sm text-slate-300">{pb.content}</p>
              </div>
            ))}
            {playbooks.length === 0 && (
              <p className="text-sm text-steel">No org playbooks yet.</p>
            )}
          </div>
        </div>
      )}

      {activeTab === "packs" && (
        <div className="grid gap-3 md:grid-cols-2">
          {packs.map((pack) => (
            <div key={pack.id} className="card p-4">
              <div className="flex items-center justify-between">
                <h3 className="font-medium text-white">{pack.name}</h3>
                <span className="text-xs text-steel">v{pack.version}</span>
              </div>
              <p className="mt-1 text-sm text-steel">{pack.description}</p>
              <div className="mt-2 flex gap-2 text-xs">
                {pack.builtin && (
                  <span className="rounded bg-cyan-500/15 px-2 py-0.5 text-cyan-400">Built-in</span>
                )}
                <span
                  className={`rounded px-2 py-0.5 ${pack.enabled ? "bg-emerald-500/15 text-emerald-400" : "bg-gray-500/15 text-gray-400"}`}
                >
                  {pack.enabled ? "Enabled" : "Disabled"}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === "sessions" && (
        <div className="space-y-3">
          {sessions.map((session) => {
            const plan = parsePlan(session.plan_json);
            return (
              <div key={session.id} className="card p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs text-steel">{new Date(session.created_at).toLocaleString()}</p>
                    <p className="mt-1 text-sm text-white">{session.message}</p>
                    {plan && (
                      <div className="mt-3 space-y-2 border-t border-navy-border pt-3">
                        <p className="text-xs text-steel">
                          Confidence: {(plan.confidence * 100).toFixed(0)}% · {plan.steps.length} step(s)
                        </p>
                        {plan.hypotheses.map((h, i) => (
                          <p key={i} className="text-xs text-slate-300">
                            • {h}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-xs capitalize ${
                      session.status === "completed"
                        ? "bg-emerald-500/15 text-emerald-400"
                        : "bg-amber-500/15 text-amber-400"
                    }`}
                  >
                    {session.status}
                  </span>
                </div>
              </div>
            );
          })}
          {sessions.length === 0 && (
            <p className="text-center text-sm text-steel">
              No agent sessions yet. Chat with Jonathan to create incident plans.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
