import { useCallback, useEffect, useRef, useState } from "react";
import { Send, User, Sparkles, Mic, Info, ShieldCheck, CheckCircle2 } from "lucide-react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { thorpeApi } from "../services/tauri";
import { useAppStore } from "../services/store";
import { buildJonathanWelcome } from "../prompts/jonathan";
import { extractFirstName } from "../lib/userName";
import { JonathanAvatar } from "../components/brand/JonathanAvatar";
import { WordByWordReply } from "../components/ui/WordByWordReply";
import { getJonathanSourceLabel, isCloudAiActive } from "../lib/jonathanMode";
import type { AiConfig, AgentPlan, AssistantChatMetadata, ConnectivityReport, KbSuggestion, RepairAction, RepairResult, RepairVerification } from "../services/types";

interface Message {
  role: "user" | "assistant";
  content: string;
  source?: string;
  repairs?: RepairResult[];
  pendingRepairs?: RepairAction[];
  pendingResolved?: boolean;
  verification?: RepairVerification | null;
  escalationCaseId?: string | null;
  agentPlan?: AgentPlan | null;
  agentSessionId?: string | null;
  kbSuggestions?: KbSuggestion[];
  connectivityReport?: ConnectivityReport | null;
}

function repairKindLabel(kind?: string): string {
  switch (kind) {
    case "mutating":
      return "Repair";
    case "diagnostic":
      return "Diagnostic";
    case "advisory":
      return "Recommendation";
    default:
      return "Action";
  }
}

function messageFromHistory(h: { role: string; content: string; metadata_json?: string | null }): Message {
  const base: Message = {
    role: h.role as "user" | "assistant",
    content: h.content,
  };
  if (!h.metadata_json) return base;
  try {
    const meta = JSON.parse(h.metadata_json) as AssistantChatMetadata;
    return {
      ...base,
      source: meta.source,
      repairs: meta.repairs_executed,
      pendingRepairs: meta.pending_repairs,
      pendingResolved: (meta.pending_repairs?.length ?? 0) === 0,
      verification: meta.verification,
      escalationCaseId: meta.escalation_case_id,
      kbSuggestions: meta.kb_suggestions,
      agentPlan: meta.agent_plan,
      agentSessionId: meta.agent_session_id,
      connectivityReport: meta.connectivity_report,
    };
  } catch {
    return base;
  }
}

export function JonathanAssistant() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [skillLevel, setSkillLevel] = useState("beginner");
  const [aiConfig, setAiConfig] = useState<AiConfig | null>(null);
  const [typingMessageIndex, setTypingMessageIndex] = useState<number | null>(null);
  const { lastScan, addNotification } = useAppStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    Promise.all([thorpeApi.getProfile(), thorpeApi.getAiConfig(), thorpeApi.getChatHistory(50)])
      .then(([profile, config, history]) => {
        setSkillLevel(profile.skill_level);
        setAiConfig(config);
        const name = extractFirstName(profile.display_name);
        const restored: Message[] = history.map(messageFromHistory);
        if (restored.length === 0) {
          setMessages([{ role: "assistant", content: buildJonathanWelcome(name) }]);
          setTypingMessageIndex(0);
        } else {
          setMessages(restored);
          setTypingMessageIndex(null);
        }
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading, typingMessageIndex, scrollToBottom]);

  const sendChat = async (userMessage: string, confirmedRepairs?: string[]): Promise<boolean> => {
    setLoading(true);
    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const response = await thorpeApi.chatWithJonathan({
        message: userMessage,
        skill_level: skillLevel,
        scan_context: lastScan ? JSON.stringify(lastScan) : undefined,
        history,
        confirmed_repairs: confirmedRepairs,
      });

      setMessages((prev) => {
        const nextIndex = prev.length;
        setTypingMessageIndex(nextIndex);
        return [
          ...prev,
          {
            role: "assistant",
            content: response.message,
            source: response.source,
            repairs: response.repairs_executed,
            pendingRepairs: response.pending_repairs,
            pendingResolved: (response.pending_repairs?.length ?? 0) === 0,
            verification: response.verification,
            escalationCaseId: response.escalation_case_id,
            agentPlan: response.agent_plan,
            agentSessionId: response.agent_session_id,
            kbSuggestions: response.kb_suggestions,
            connectivityReport: response.connectivity_report,
          },
        ];
      });

      const mutating = response.repairs_executed?.filter(
        (r) => r.success && r.action_kind === "mutating"
      ).length ?? 0;
      if (mutating > 0) {
        addNotification({
          type: "success",
          title: "Repairs applied",
          message: `${mutating} repair(s) completed on your system.`,
        });
      }
      if (response.verification?.improved) {
        addNotification({
          type: "success",
          title: "Verification passed",
          message: `Health score improved to ${response.verification.health_after}/100.`,
        });
      }
      if (response.escalation_case_id) {
        addNotification({
          type: "info",
          title: "Case escalated",
          message: "A support case was opened in Technician Workspace.",
        });
      }
      return true;
    } catch (err) {
      addNotification({
        type: "error",
        title: "Chat Error",
        message: String(err),
      });
      return false;
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    await sendChat(userMessage);
  };

  const approveMessageRepairs = async (messageIndex: number, repairs: RepairAction[]) => {
    if (repairs.length === 0 || loading) return;
    const ids = repairs.map((p) => p.id);
    const names = repairs.map((p) => p.name);
    const userMessage = `Approve and run: ${names.join(", ")}`;

    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    const ok = await sendChat(userMessage, ids);
    if (ok) {
      setMessages((prev) =>
        prev.map((m, idx) =>
          idx === messageIndex ? { ...m, pendingRepairs: [], pendingResolved: true } : m
        )
      );
    }
  };

  const cloudAiActive = aiConfig ? isCloudAiActive(aiConfig) : false;

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col animate-fade-in">
      <div className="card-brand mb-4 flex items-center justify-between gap-4 p-4">
        <div className="flex items-center gap-4">
          <JonathanAvatar size="md" />
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-thorpe-primary">
              AI Technician
            </p>
            <h1 className="font-display text-xl font-bold tracking-[0.08em] text-white">JONATHAN</h1>
            <p className="text-sm text-steel">
              {cloudAiActive
                ? "Cloud AI enabled — I run repairs, verify results, and summarize with GPT."
                : "Autonomous technician — safe diagnostics and repairs with verification."}
            </p>
          </div>
        </div>
        <select
          value={skillLevel}
          onChange={(e) => setSkillLevel(e.target.value)}
          className="input w-auto shrink-0 text-sm"
        >
          <option value="beginner">Beginner explanations</option>
          <option value="advanced">Advanced explanations</option>
        </select>
      </div>

      <div className="mb-4 flex items-start gap-3 rounded-xl border border-thorpe-primary/20 bg-thorpe-primary/5 px-4 py-3 text-sm text-slate-300">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-thorpe-primary" />
        <p>
          {cloudAiActive ? (
            <>
              <span className="font-medium text-white">Cloud AI mode.</span> Repairs still run locally;
              mutating actions require your approval before execution.
            </>
          ) : aiConfig?.enabled ? (
            <>
              <span className="font-medium text-warning">Cloud AI enabled but not active.</span> Add
              your API key in Settings → Jonathan AI (Cloud).
            </>
          ) : (
            <>
              <span className="font-medium text-white">Autonomous mode.</span> I run diagnostics
              automatically; system-changing repairs need your approval.
            </>
          )}
          {lastScan ? " Using your latest scan for context." : " Run a scan first for deeper analysis."}
        </p>
      </div>

      <div className="card flex flex-1 flex-col overflow-hidden p-0">
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.map((msg, i) => {
            const isTyping = msg.role === "assistant" && typingMessageIndex === i;

            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
              >
                {msg.role === "user" ? (
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-navy-border">
                    <User className="h-4 w-4 text-steel" />
                  </div>
                ) : (
                  <JonathanAvatar size="sm" showRing={false} />
                )}
                <div
                  className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-thorpe-primary text-white shadow-brand"
                      : "border border-navy-border bg-navy-light text-slate-200"
                  }`}
                >
                  {msg.role === "user" ? (
                    msg.content
                  ) : (
                    <WordByWordReply
                      content={msg.content}
                      animate={isTyping}
                      onComplete={() => setTypingMessageIndex(null)}
                      onProgress={scrollToBottom}
                    />
                  )}
                  {msg.source && msg.role === "assistant" && !isTyping && (
                    <p className="mt-2 flex items-center gap-1 text-xs text-steel">
                      <Sparkles className="h-3 w-3 text-cyber-teal" />
                      {getJonathanSourceLabel(msg.source)}
                    </p>
                  )}
                  {msg.verification && msg.role === "assistant" && !isTyping && (
                    <p className="mt-2 flex items-center gap-1 text-xs text-emerald-400">
                      <ShieldCheck className="h-3 w-3" />
                      Verified: health {msg.verification.health_before} → {msg.verification.health_after}
                      {msg.verification.improved && " ✓"}
                    </p>
                  )}
                  {msg.escalationCaseId && msg.role === "assistant" && !isTyping && (
                    <p className="mt-2 text-xs text-amber-300">
                      Case{" "}
                      <Link to="/workspace" className="underline">
                        {msg.escalationCaseId.slice(0, 8)}…
                      </Link>{" "}
                      opened in Workspace.
                    </p>
                  )}
                  {msg.kbSuggestions && msg.kbSuggestions.length > 0 && !isTyping && (
                    <div className="mt-3 space-y-1 border-t border-navy-border/60 pt-2">
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-steel">
                        Related knowledge
                      </p>
                      {msg.kbSuggestions.map((kb) => (
                        <Link
                          key={kb.id}
                          to={`/knowledge`}
                          className="block text-xs text-thorpe-primary hover:underline"
                        >
                          {kb.title}
                          {kb.source && <span className="text-steel"> · {kb.source}</span>}
                        </Link>
                      ))}
                    </div>
                  )}
                  {msg.connectivityReport && msg.role === "assistant" && !isTyping && (
                    <div className="mt-3 space-y-2 border-t border-navy-border/60 pt-2">
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-steel">
                        Offline connectivity · {msg.connectivityReport.overall_status}
                      </p>
                      <p className="text-xs text-slate-300">{msg.connectivityReport.playbook_summary}</p>
                      <div className="space-y-1">
                        {msg.connectivityReport.checks.map((check) => (
                          <p key={check.name} className="text-xs text-steel">
                            <span
                              className={
                                check.status === "pass"
                                  ? "text-emerald-400"
                                  : check.status === "fail"
                                    ? "text-warning"
                                    : "text-slate-400"
                              }
                            >
                              {check.status === "pass" ? "✓" : check.status === "fail" ? "✗" : "!"}
                            </span>{" "}
                            <span className="text-slate-300">{check.name}</span> — {check.detail}
                          </p>
                        ))}
                      </div>
                    </div>
                  )}
                  {msg.agentPlan && msg.role === "assistant" && !isTyping && (
                    <div className="mt-3 space-y-2 border-t border-navy-border/60 pt-2">
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-steel">
                        Incident plan · {(msg.agentPlan.confidence * 100).toFixed(0)}% confidence
                      </p>
                      {msg.agentPlan.hypotheses.map((h, idx) => (
                        <p key={idx} className="text-xs text-slate-300">
                          • {h}
                        </p>
                      ))}
                      {msg.agentPlan.steps.length > 0 && (
                        <div className="mt-1 space-y-1">
                          {msg.agentPlan.steps.map((step) => (
                            <p key={step.tool_id} className="text-xs text-steel">
                              <span className="text-cyber-teal">{step.tool_id}</span>
                              {step.requires_approval && (
                                <span className="ml-1 text-amber-400">(approval required)</span>
                              )}
                              — {step.reason}
                            </p>
                          ))}
                        </div>
                      )}
                      {msg.agentPlan.citations.length > 0 && (
                        <p className="text-xs text-steel">
                          Citations: {msg.agentPlan.citations.join(", ")}
                        </p>
                      )}
                      {msg.agentSessionId && (
                        <p className="text-xs text-steel">
                          Session{" "}
                          <Link
                            to={`/intelligence?tab=sessions&session=${msg.agentSessionId}`}
                            className="text-thorpe-primary underline"
                          >
                            {msg.agentSessionId.slice(0, 8)}…
                          </Link>
                        </p>
                      )}
                    </div>
                  )}
                  {msg.pendingRepairs &&
                    msg.pendingRepairs.length > 0 &&
                    !msg.pendingResolved &&
                    msg.role === "assistant" &&
                    !isTyping && (
                      <div className="mt-3 flex items-center justify-between gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2">
                        <p className="text-xs text-amber-100">
                          <span className="font-medium">Approval needed:</span>{" "}
                          {msg.pendingRepairs.map((p) => p.name).join(", ")}
                        </p>
                        <button
                          onClick={() => approveMessageRepairs(i, msg.pendingRepairs!)}
                          disabled={loading}
                          className="btn-primary shrink-0 px-3 py-1 text-xs"
                        >
                          Approve
                        </button>
                      </div>
                    )}
                  {msg.repairs && msg.repairs.length > 0 && !isTyping && (
                    <div className="mt-3 space-y-1 border-t border-navy-border/60 pt-2">
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-steel">
                        Actions taken
                      </p>
                      {msg.repairs.map((repair) => (
                        <p
                          key={repair.record_id || repair.action_id}
                          className={`text-xs ${repair.success ? "text-success" : "text-warning"}`}
                        >
                          {repair.success ? "✓" : "⚠"}{" "}
                          <span className="text-steel">[{repairKindLabel(repair.action_kind)}]</span>{" "}
                          {repair.action_name || repair.message}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            );
          })}
          {loading && (
            <div className="flex gap-3">
              <JonathanAvatar size="sm" showRing={false} />
              <div className="rounded-2xl border border-navy-border bg-navy-light px-4 py-3">
                <div className="flex gap-1">
                  <span className="h-2 w-2 animate-pulse rounded-full bg-thorpe-primary" />
                  <span className="h-2 w-2 animate-pulse rounded-full bg-thorpe-primary [animation-delay:0.2s]" />
                  <span className="h-2 w-2 animate-pulse rounded-full bg-thorpe-primary [animation-delay:0.4s]" />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="border-t border-navy-border bg-navy-light/30 p-4">
          <div className="flex gap-3">
            <button
              type="button"
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-cyber-teal/30 bg-cyber-teal/10 text-cyber-teal transition-colors hover:bg-cyber-teal/20"
              title="Voice input (coming soon)"
              disabled
            >
              <Mic className="h-4 w-4" />
            </button>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
              placeholder="Describe your IT issue..."
              className="input flex-1"
              disabled={loading}
            />
            <button onClick={sendMessage} disabled={loading || !input.trim()} className="btn-primary">
              <Send className="h-4 w-4" />
            </button>
          </div>
          <p className="mt-2 flex items-center gap-1 text-xs text-steel">
            <CheckCircle2 className="h-3 w-3" />
            Jonathan never requests passwords. Mutating repairs require explicit approval.
          </p>
        </div>
      </div>
    </div>
  );
}
