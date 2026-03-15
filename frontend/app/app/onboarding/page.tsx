"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { api } from "@/services/api";
import type { OnboardingRecommendationResponse, OnboardingStateRead, WorkerInstanceExecuteResponse, WorkerTemplateRead } from "@/types";

const STEPS = ["welcome", "workspace_setup", "goal_selection", "recommendations", "first_success"] as const;

export default function OnboardingPage() {
  const router = useRouter();
  const [state, setState] = useState<OnboardingStateRead | null>(null);
  const [recommendations, setRecommendations] = useState<OnboardingRecommendationResponse | null>(null);
  const [templates, setTemplates] = useState<WorkerTemplateRead[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [selectedGoal, setSelectedGoal] = useState<OnboardingStateRead["goal_category"]>("sales");

  const currentStep = state?.current_step || "welcome";
  const currentIndex = Math.max(STEPS.indexOf(currentStep as (typeof STEPS)[number]), 0);

  const progress = useMemo(() => `${Math.min(currentIndex + 1, STEPS.length)}/${STEPS.length}`, [currentIndex]);

  const load = async () => {
    setError("");
    const [stateRes, templateRes] = await Promise.all([
      api.get<OnboardingStateRead>("/onboarding/state"),
      api.get<WorkerTemplateRead[]>("/workers/templates?include_public=true")
    ]);
    setState(stateRes);
    setTemplates(templateRes);
    if (stateRes.goal_category) setSelectedGoal(stateRes.goal_category);
  };

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load onboarding"));
  }, []);

  const patchState = async (payload: Record<string, unknown>) => {
    setBusy(true);
    try {
      const updated = await api.patch<OnboardingStateRead>("/onboarding/state", payload);
      setState(updated);
      return updated;
    } finally {
      setBusy(false);
    }
  };

  const nextStep = async () => {
    const next = STEPS[Math.min(currentIndex + 1, STEPS.length - 1)];
    await patchState({ current_step: next, complete_step: currentStep });
  };

  const skipOnboarding = async () => {
    await patchState({ is_skipped: true, is_completed: false });
    router.push("/app");
  };

  const loadRecommendations = async (goal: string) => {
    const data = await api.get<OnboardingRecommendationResponse>(`/onboarding/recommendations?goal_category=${goal}&limit=5`);
    setRecommendations(data);
    await patchState({ goal_category: goal, complete_step: "goal_selection", current_step: "recommendations" });
  };

  const installAndRunFirstWorker = async (slug: string) => {
    setBusy(true);
    try {
      const template = templates.find((item) => item.slug === slug);
      if (!template) throw new Error("Template is not available in your workspace catalog");
      const instance = await api.post<{ id: string; name: string }>(`/workers/templates/${template.id}/install`, {
        instance_name: `${template.display_name} Instance`,
        runtime_config_overrides: {},
        memory_scope: "instance"
      });
      const run = await api.post<WorkerInstanceExecuteResponse>(`/workers/instances/${instance.id}/run`, {
        runtime_input: { source: "onboarding_first_run" },
        trigger_source: "onboarding"
      });
      setMessage(`Installed "${instance.name}" and started run ${run.run_id.slice(0, 8)}…`);
      await patchState({ current_step: "first_success", complete_step: "recommendations" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to install and run starter worker");
    } finally {
      setBusy(false);
    }
  };

  const completeOnboarding = async () => {
    await patchState({ is_completed: true, complete_step: "first_success" });
    router.push("/app");
  };

  if (error && !state) return <ErrorState message={error} />;
  if (!state) return <LoadingState label="Loading onboarding..." />;

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <div className="card p-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-2xl font-semibold">Launch Onboarding</h2>
            <p className="text-sm text-slate-600">Complete your first worker setup in a few guided steps.</p>
          </div>
          <div className="text-sm text-slate-600">Step {progress}</div>
        </div>
      </div>

      {error ? <ErrorState message={error} /> : null}
      {message ? <div className="card border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</div> : null}

      {currentStep === "welcome" ? (
        <div className="card space-y-3 p-5">
          <h3 className="text-xl font-semibold">Welcome — what do you want to do first?</h3>
          <div className="grid gap-2 md:grid-cols-2">
            {["Explore marketplace", "Build a worker", "Install starter workers", "Set up workspace"].map((path) => (
              <label key={path} className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm">
                <input
                  type="checkbox"
                  checked={(state.selected_paths_json || []).includes(path.toLowerCase().replace(/\s+/g, "_"))}
                  onChange={(event) => {
                    const key = path.toLowerCase().replace(/\s+/g, "_");
                    const existing = new Set(state.selected_paths_json || []);
                    if (event.target.checked) existing.add(key);
                    else existing.delete(key);
                    void patchState({ selected_paths_json: Array.from(existing) });
                  }}
                />
                {path}
              </label>
            ))}
          </div>
          <div className="flex gap-2">
            <button className="btn-primary" disabled={busy} onClick={() => void nextStep()}>Continue</button>
            <button className="btn-secondary" disabled={busy} onClick={() => void skipOnboarding()}>Skip for now</button>
          </div>
        </div>
      ) : null}

      {currentStep === "workspace_setup" ? (
        <div className="card space-y-3 p-5">
          <h3 className="text-xl font-semibold">Workspace setup</h3>
          <p className="text-sm text-slate-600">You can refine workspace settings anytime from Settings.</p>
          <div className="flex gap-2">
            <button className="btn-primary" disabled={busy} onClick={() => void nextStep()}>Continue</button>
            <button className="btn-secondary" disabled={busy} onClick={() => router.push("/app/settings")}>Open settings</button>
          </div>
        </div>
      ) : null}

      {currentStep === "goal_selection" ? (
        <div className="card space-y-3 p-5">
          <h3 className="text-xl font-semibold">Choose your primary goal</h3>
          <div className="grid gap-2 sm:grid-cols-2 md:grid-cols-3">
            {["real_estate", "marketing", "sales", "ecommerce", "research", "operations", "custom"].map((goal) => (
              <button
                key={goal}
                className={`rounded-lg border px-3 py-2 text-sm ${selectedGoal === goal ? "border-brand-500 bg-brand-50 text-brand-700" : "border-slate-200 text-slate-700"}`}
                onClick={() => setSelectedGoal(goal as OnboardingStateRead["goal_category"])}
              >
                {goal.replace("_", " ")}
              </button>
            ))}
          </div>
          <button className="btn-primary" disabled={busy} onClick={() => void loadRecommendations(selectedGoal || "sales")}>
            Get recommendations
          </button>
        </div>
      ) : null}

      {currentStep === "recommendations" ? (
        <div className="card space-y-3 p-5">
          <h3 className="text-xl font-semibold">Recommended starter workers</h3>
          <p className="text-sm text-slate-600">Install one to create your first success moment.</p>
          {!recommendations?.templates.length ? (
            <button className="btn-secondary" disabled={busy} onClick={() => void loadRecommendations(selectedGoal || "sales")}>
              Load recommendations
            </button>
          ) : (
            <div className="space-y-2">
              {recommendations.templates.map((item) => (
                <div key={item.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200 px-3 py-2">
                  <div>
                    <p className="font-medium">{item.name}</p>
                    <p className="text-xs text-slate-500">{item.category} · {item.short_description || "Starter worker"}</p>
                  </div>
                  <button className="btn-primary px-3 py-1 text-xs" disabled={busy} onClick={() => void installAndRunFirstWorker(item.slug)}>
                    Install + Run
                  </button>
                </div>
              ))}
            </div>
          )}
          <div className="flex gap-2">
            <button className="btn-secondary" disabled={busy} onClick={() => router.push("/app/worker-builder")}>Build custom worker instead</button>
          </div>
        </div>
      ) : null}

      {currentStep === "first_success" ? (
        <div className="card space-y-3 p-5">
          <h3 className="text-xl font-semibold">You’re ready to launch</h3>
          <p className="text-sm text-slate-600">
            Great work. You can now run workers, review analytics, and explore upgrades as your workload grows.
          </p>
          <div className="flex flex-wrap gap-2">
            <button className="btn-primary" disabled={busy} onClick={() => void completeOnboarding()}>Finish onboarding</button>
            <button className="btn-secondary" onClick={() => router.push("/pricing")}>Review plans</button>
            <button className="btn-secondary" onClick={() => router.push("/app/marketplace")}>Explore marketplace</button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
