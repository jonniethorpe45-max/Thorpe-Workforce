import type { AgentPlan, ScanIssue, WatchdogEvent } from "../services/types";

export interface WatchdogHandoff {
  eventId: string;
  eventType: string;
  message: string;
  healthScore: number;
  plan?: AgentPlan | null;
  issues?: ScanIssue[];
}

export function watchdogEventLabel(eventType: string): string {
  if (eventType === "health_threshold") return "Health score";
  if (eventType === "high_cpu" || eventType === "high_cpu_process") return "CPU spike";
  if (eventType === "high_memory") return "Memory pressure";
  if (eventType.startsWith("low_disk")) return "Low disk space";
  return "System alert";
}

export function parseWatchdogPlan(planJson: string | null | undefined): AgentPlan | null {
  if (!planJson) return null;
  try {
    return JSON.parse(planJson) as AgentPlan;
  } catch {
    return null;
  }
}

export function parseWatchdogIssues(issuesJson: string | null | undefined): ScanIssue[] {
  if (!issuesJson) return [];
  try {
    return JSON.parse(issuesJson) as ScanIssue[];
  } catch {
    return [];
  }
}

export function handoffFromWatchdogEvent(event: WatchdogEvent): WatchdogHandoff {
  return {
    eventId: event.id,
    eventType: event.event_type,
    message: event.message,
    healthScore: event.health_score,
    plan: parseWatchdogPlan(event.plan_json),
    issues: parseWatchdogIssues(event.issues_json),
  };
}

export function buildWatchdogJonathanPrompt(handoff: WatchdogHandoff): string {
  const label = watchdogEventLabel(handoff.eventType);
  return `Watchdog alert (${label}): ${handoff.message} Health score is ${handoff.healthScore}/100. Please investigate and recommend safe repairs.`;
}
