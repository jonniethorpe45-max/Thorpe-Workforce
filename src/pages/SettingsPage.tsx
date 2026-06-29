import { useEffect, useState } from "react";
import { User, Bot, Shield, Trash2, Webhook, Radar, MessageSquare } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { thorpeApi } from "../services/tauri";
import { useAppStore } from "../services/store";
import { handoffFromWatchdogEvent, parseWatchdogIssues, watchdogEventLabel } from "../lib/watchdog";
import type { AiConfig, Profile, PsaConfig, WatchdogConfig, WatchdogEvent } from "../services/types";

export function SettingsPage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [aiConfig, setAiConfig] = useState<AiConfig | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [appInfo, setAppInfo] = useState<{ name: string; version: string; platform: string; data_dir: string } | null>(null);
  const [psaConfig, setPsaConfig] = useState<PsaConfig | null>(null);
  const [psaSecret, setPsaSecret] = useState("");
  const [watchdogConfig, setWatchdogConfig] = useState<WatchdogConfig | null>(null);
  const [watchdogEvents, setWatchdogEvents] = useState<WatchdogEvent[]>([]);
  const { addNotification, setWatchdogHandoff } = useAppStore();
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      thorpeApi.getProfile(),
      thorpeApi.getAiConfig(),
      thorpeApi.getAppInfo(),
      thorpeApi.getPsaSettings(),
      thorpeApi.getWatchdogStatus(),
    ])
      .then(([p, a, info, psa, watchdog]) => {
        setProfile(p);
        setAiConfig(a);
        setAppInfo(info);
        setPsaConfig(psa);
        setWatchdogConfig(watchdog.config);
        setWatchdogEvents(watchdog.recent_events);
      })
      .catch((err) => {
        addNotification({ type: "error", title: "Settings load failed", message: String(err) });
      });
  }, [addNotification]);

  const saveProfile = async () => {
    if (!profile) return;
    try {
      const updated = await thorpeApi.updateProfile(
        profile.display_name,
        profile.email,
        profile.skill_level
      );
      setProfile(updated);
      addNotification({ type: "success", title: "Profile Saved", message: "Your profile has been updated." });
    } catch (err) {
      addNotification({ type: "error", title: "Save Failed", message: String(err) });
    }
  };

  const saveAiConfig = async () => {
    if (!aiConfig) return;

    const hasNewKey = Boolean(apiKeyInput.trim());
    if (aiConfig.enabled && !aiConfig.api_key_configured && !hasNewKey) {
      addNotification({
        type: "error",
        title: "API Key Required",
        message: "Enter your OpenAI API key before enabling Cloud AI.",
      });
      return;
    }

    try {
      await thorpeApi.setAiConfig({
        provider: aiConfig.provider,
        model: aiConfig.model,
        base_url: aiConfig.base_url,
        enabled: aiConfig.enabled,
        api_key: apiKeyInput.trim() || undefined,
      });
      setApiKeyInput("");
      const refreshed = await thorpeApi.getAiConfig();
      setAiConfig(refreshed);
      const status = refreshed.enabled && refreshed.api_key_configured
        ? "Cloud AI is active."
        : refreshed.enabled
          ? "Cloud AI is enabled but needs a valid API key."
          : "Jonathan will use local autonomous repair mode.";
      addNotification({ type: "success", title: "AI Settings Saved", message: status });
    } catch (err) {
      addNotification({ type: "error", title: "Save Failed", message: String(err) });
    }
  };

  const deleteAllData = async () => {
    if (!confirm("This will permanently delete all your data. This cannot be undone. Continue?")) return;
    if (!confirm("Are you absolutely sure? All scans, reports, and chat history will be deleted.")) return;
    try {
      await thorpeApi.deleteAllUserData();
      addNotification({ type: "success", title: "Data Deleted", message: "All user data has been removed." });
    } catch (err) {
      addNotification({ type: "error", title: "Delete Failed", message: String(err) });
    }
  };

  const savePsaConfig = async () => {
    if (!psaConfig) return;
    try {
      const updated = await thorpeApi.updatePsaSettings(
        psaConfig.enabled,
        psaConfig.webhook_url,
        psaConfig.provider,
        psaSecret.trim() || undefined
      );
      setPsaConfig(updated);
      setPsaSecret("");
      addNotification({ type: "success", title: "PSA Saved", message: "PSA webhook settings updated." });
    } catch (err) {
      addNotification({ type: "error", title: "Save Failed", message: String(err) });
    }
  };

  const testPsaWebhook = async () => {
    if (!psaConfig) return;
    try {
      const result = await thorpeApi.testPsaWebhook(
        psaConfig.webhook_url?.trim() || undefined,
        psaSecret.trim() || undefined
      );
      addNotification({
        type: result.success ? "success" : "error",
        title: result.success ? "Webhook OK" : "Webhook Failed",
        message: result.message,
      });
    } catch (err) {
      addNotification({ type: "error", title: "Test Failed", message: String(err) });
    }
  };

  const saveWatchdogConfig = async () => {
    if (!watchdogConfig) return;
    try {
      const updated = await thorpeApi.updateWatchdogConfig(
        watchdogConfig.enabled,
        watchdogConfig.interval_minutes,
        watchdogConfig.health_threshold,
        watchdogConfig.auto_notify,
        watchdogConfig.auto_plan
      );
      setWatchdogConfig(updated);
      const status = await thorpeApi.getWatchdogStatus();
      setWatchdogEvents(status.recent_events);
      addNotification({ type: "success", title: "Watchdog Saved", message: "Proactive monitoring settings updated." });
    } catch (err) {
      addNotification({ type: "error", title: "Save Failed", message: String(err) });
    }
  };

  const acknowledgeWatchdogEvent = async (eventId: string) => {
    try {
      await thorpeApi.acknowledgeWatchdogEvent(eventId);
      setWatchdogEvents((prev) =>
        prev.map((e) => (e.id === eventId ? { ...e, acknowledged: true } : e))
      );
    } catch (err) {
      addNotification({ type: "error", title: "Acknowledge failed", message: String(err) });
    }
  };

  const sendWatchdogToJonathan = (event: (typeof watchdogEvents)[number]) => {
    setWatchdogHandoff(handoffFromWatchdogEvent(event));
    navigate("/jonathan");
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="mt-1 text-gray-400">Manage your profile, AI, and privacy preferences.</p>
      </div>

      <section className="card space-y-4">
        <div className="flex items-center gap-2">
          <User className="h-5 w-5 text-thorpe-400" />
          <h2 className="font-medium text-white">Profile</h2>
        </div>
        {profile && (
          <>
            <div>
              <label className="mb-1 block text-xs text-gray-400">Display Name</label>
              <input
                className="input"
                value={profile.display_name}
                onChange={(e) => setProfile({ ...profile, display_name: e.target.value })}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-400">Email (optional)</label>
              <input
                className="input"
                type="email"
                value={profile.email || ""}
                onChange={(e) => setProfile({ ...profile, email: e.target.value || null })}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-400">Skill Level</label>
              <select
                className="input"
                value={profile.skill_level}
                onChange={(e) => setProfile({ ...profile, skill_level: e.target.value })}
              >
                <option value="beginner">Beginner</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>
            <button onClick={saveProfile} className="btn-primary text-sm">Save Profile</button>
          </>
        )}
      </section>

      <section className="card space-y-4">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-thorpe-400" />
          <h2 className="font-medium text-white">Jonathan AI (Cloud)</h2>
        </div>
        <p className="text-sm text-gray-400">
          Enable cloud AI for enhanced responses. Jonathan works offline without this — your API key
          is stored locally and never shared.
        </p>
        {aiConfig && (
          <>
            <label className="flex items-center gap-2 text-sm text-gray-300">
              <input
                type="checkbox"
                checked={aiConfig.enabled}
                onChange={(e) => setAiConfig({ ...aiConfig, enabled: e.target.checked })}
                className="rounded border-surface-border"
              />
              Enable cloud AI
            </label>
            <div>
              <label className="mb-1 block text-xs text-gray-400">API Key</label>
              <input
                className="input font-mono"
                type="password"
                placeholder={aiConfig.api_key_configured ? "Key configured — enter a new key to replace" : "sk-..."}
                value={apiKeyInput}
                onChange={(e) => setApiKeyInput(e.target.value)}
              />
              {aiConfig.api_key_configured && !apiKeyInput && (
                <p className="mt-1 text-xs text-gray-500">An API key is stored securely on this device.</p>
              )}
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-400">Model</label>
              <input
                className="input"
                value={aiConfig.model}
                onChange={(e) => setAiConfig({ ...aiConfig, model: e.target.value })}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-400">Base URL</label>
              <input
                className="input"
                value={aiConfig.base_url}
                onChange={(e) => setAiConfig({ ...aiConfig, base_url: e.target.value })}
              />
            </div>
            <button onClick={saveAiConfig} className="btn-primary text-sm">Save AI Settings</button>
            <p
              className={`text-xs ${
                aiConfig.enabled && aiConfig.api_key_configured
                  ? "text-success"
                  : aiConfig.enabled
                    ? "text-warning"
                    : "text-gray-500"
              }`}
            >
              {aiConfig.enabled && aiConfig.api_key_configured
                ? "Status: Cloud AI active — Jonathan will use your API key for responses."
                : aiConfig.enabled
                  ? "Status: Cloud AI enabled — add and save an API key to activate."
                  : "Status: Local autonomous repair mode (no API key required)."}
            </p>
          </>
        )}
      </section>

      <section className="card space-y-4">
        <div className="flex items-center gap-2">
          <Webhook className="h-5 w-5 text-thorpe-400" />
          <h2 className="font-medium text-white">PSA Integration</h2>
        </div>
        <p className="text-sm text-gray-400">
          Outbound webhooks for case and agent session events (ConnectWise, Halo, generic).
        </p>
        {psaConfig && (
          <>
            <label className="flex items-center gap-2 text-sm text-gray-300">
              <input
                type="checkbox"
                checked={psaConfig.enabled}
                onChange={(e) => setPsaConfig({ ...psaConfig, enabled: e.target.checked })}
                className="rounded border-surface-border"
              />
              Enable PSA webhooks
            </label>
            <div>
              <label className="mb-1 block text-xs text-gray-400">Webhook URL</label>
              <input
                className="input font-mono text-sm"
                value={psaConfig.webhook_url || ""}
                onChange={(e) =>
                  setPsaConfig({ ...psaConfig, webhook_url: e.target.value || null })
                }
                placeholder="https://your-psa.example/webhook"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-400">Provider</label>
              <select
                className="input"
                value={psaConfig.provider}
                onChange={(e) => setPsaConfig({ ...psaConfig, provider: e.target.value })}
              >
                <option value="generic">Generic</option>
                <option value="connectwise">ConnectWise</option>
                <option value="halo">Halo PSA</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-400">HMAC Secret (optional)</label>
              <input
                className="input font-mono"
                type="password"
                value={psaSecret}
                onChange={(e) => setPsaSecret(e.target.value)}
                placeholder="Signing secret for X-Thorpe-Signature"
              />
            </div>
            <div className="flex gap-2">
              <button onClick={savePsaConfig} className="btn-primary text-sm">
                Save PSA
              </button>
              <button onClick={testPsaWebhook} className="btn-secondary text-sm">
                Test webhook
              </button>
            </div>
          </>
        )}
      </section>

      <section className="card space-y-4">
        <div className="flex items-center gap-2">
          <Radar className="h-5 w-5 text-thorpe-400" />
          <h2 className="font-medium text-white">Proactive Watchdog</h2>
        </div>
        <p className="text-sm text-gray-400">
          Background monitoring for CPU spikes, memory pressure, low disk space, and overall health.
          Alerts can be sent to Jonathan with a pre-built repair plan.
        </p>
        {watchdogConfig && (
          <>
            <label className="flex items-center gap-2 text-sm text-gray-300">
              <input
                type="checkbox"
                checked={watchdogConfig.enabled}
                onChange={(e) => setWatchdogConfig({ ...watchdogConfig, enabled: e.target.checked })}
                className="rounded border-surface-border"
              />
              Enable watchdog
            </label>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs text-gray-400">Check interval (minutes)</label>
                <input
                  className="input"
                  type="number"
                  min={5}
                  value={watchdogConfig.interval_minutes}
                  onChange={(e) =>
                    setWatchdogConfig({
                      ...watchdogConfig,
                      interval_minutes: parseInt(e.target.value, 10) || 5,
                    })
                  }
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-gray-400">Health threshold</label>
                <input
                  className="input"
                  type="number"
                  min={0}
                  max={100}
                  value={watchdogConfig.health_threshold}
                  onChange={(e) =>
                    setWatchdogConfig({
                      ...watchdogConfig,
                      health_threshold: parseInt(e.target.value, 10) || 70,
                    })
                  }
                />
              </div>
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-300">
              <input
                type="checkbox"
                checked={watchdogConfig.auto_notify}
                onChange={(e) =>
                  setWatchdogConfig({ ...watchdogConfig, auto_notify: e.target.checked })
                }
                className="rounded border-surface-border"
              />
              Desktop notifications on breach
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-300">
              <input
                type="checkbox"
                checked={watchdogConfig.auto_plan}
                onChange={(e) =>
                  setWatchdogConfig({ ...watchdogConfig, auto_plan: e.target.checked })
                }
                className="rounded border-surface-border"
              />
              Auto-generate response plan
            </label>
            <button onClick={saveWatchdogConfig} className="btn-primary text-sm">
              Save Watchdog
            </button>
            {watchdogEvents.length > 0 && (
              <div className="space-y-2 border-t border-surface-border pt-4">
                <h3 className="text-sm font-medium text-white">Recent alerts</h3>
                {watchdogEvents.map((event) => {
                  const issues = parseWatchdogIssues(event.issues_json);
                  return (
                  <div
                    key={event.id}
                    className={`rounded-lg border p-3 text-sm ${
                      event.acknowledged
                        ? "border-surface-border text-gray-500"
                        : "border-amber-500/30 text-amber-100"
                    }`}
                  >
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-200">
                        {watchdogEventLabel(event.event_type)}
                      </span>
                      <span className="text-xs text-gray-500">Health {event.health_score}/100</span>
                    </div>
                    <p>{event.message}</p>
                    {issues.length > 0 && (
                      <ul className="mt-2 space-y-1 text-xs text-gray-400">
                        {issues.slice(0, 3).map((issue) => (
                          <li key={issue.id}>• {issue.title}</li>
                        ))}
                      </ul>
                    )}
                    <p className="mt-1 text-xs text-gray-500">
                      {new Date(event.created_at).toLocaleString()}
                    </p>
                    {!event.acknowledged && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => sendWatchdogToJonathan(event)}
                          className="btn-primary inline-flex items-center gap-1 px-3 py-1 text-xs"
                        >
                          <MessageSquare className="h-3.5 w-3.5" />
                          Send to Jonathan
                        </button>
                        <button
                          type="button"
                          onClick={() => acknowledgeWatchdogEvent(event.id)}
                          className="btn-secondary px-3 py-1 text-xs"
                        >
                          Acknowledge
                        </button>
                      </div>
                    )}
                  </div>
                  );
                })}
              </div>
            )}
          </>
        )}
      </section>

      <section className="card space-y-4">
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-thorpe-400" />
          <h2 className="font-medium text-white">Privacy & Data</h2>
        </div>
        {appInfo && (
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Version</span>
              <span className="text-gray-200">{appInfo.version}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Platform</span>
              <span className="text-gray-200">{appInfo.platform}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Data Directory</span>
              <span className="max-w-xs truncate text-gray-200">{appInfo.data_dir}</span>
            </div>
          </div>
        )}
        <p className="text-xs text-gray-500">
          All data is stored locally on your device. See PRIVACY.md and SECURITY.md for details.
        </p>
        <button onClick={deleteAllData} className="btn-danger text-sm">
          <Trash2 className="h-4 w-4" /> Delete All User Data
        </button>
      </section>
    </div>
  );
}
