import { useEffect, useState } from "react";
import { User, Bot, Shield, Trash2 } from "lucide-react";
import { thorpeApi } from "../services/tauri";
import { useAppStore } from "../services/store";
import type { AiConfig, Profile } from "../services/types";

export function SettingsPage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [aiConfig, setAiConfig] = useState<AiConfig | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [appInfo, setAppInfo] = useState<{ name: string; version: string; platform: string; data_dir: string } | null>(null);
  const { addNotification } = useAppStore();

  useEffect(() => {
    Promise.all([thorpeApi.getProfile(), thorpeApi.getAiConfig(), thorpeApi.getAppInfo()]).then(
      ([p, a, info]) => {
        setProfile(p);
        setAiConfig(a);
        setAppInfo(info);
      }
    );
  }, []);

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
