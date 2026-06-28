import { useCallback, useEffect, useRef, useState } from "react";
import { Send, User, Sparkles, Mic, Info } from "lucide-react";
import { motion } from "framer-motion";
import { thorpeApi } from "../services/tauri";
import { useAppStore } from "../services/store";
import { buildJonathanWelcome } from "../prompts/jonathan";
import { extractFirstName } from "../lib/userName";
import { JonathanAvatar } from "../components/brand/JonathanAvatar";
import { WordByWordReply } from "../components/ui/WordByWordReply";
import { getJonathanSourceLabel, isCloudAiActive } from "../lib/jonathanMode";
import type { AiConfig, RepairResult } from "../services/types";

interface Message {
  role: "user" | "assistant";
  content: string;
  source?: string;
  repairs?: RepairResult[];
}

export function JonathanAssistant() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [skillLevel, setSkillLevel] = useState("beginner");
  const [aiConfig, setAiConfig] = useState<AiConfig | null>(null);
  const [typingMessageIndex, setTypingMessageIndex] = useState<number | null>(0);
  const { lastScan, addNotification } = useAppStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    Promise.all([thorpeApi.getProfile(), thorpeApi.getAiConfig()])
      .then(([profile, config]) => {
        setSkillLevel(profile.skill_level);
        setAiConfig(config);
        const name = extractFirstName(profile.display_name);
        setMessages([{ role: "assistant", content: buildJonathanWelcome(name) }]);
        setTypingMessageIndex(0);
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading, typingMessageIndex]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const response = await thorpeApi.chatWithJonathan({
        message: userMessage,
        skill_level: skillLevel,
        scan_context: lastScan ? JSON.stringify(lastScan) : undefined,
        history,
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
          },
        ];
      });

      if (response.repairs_executed && response.repairs_executed.length > 0) {
        const fixed = response.repairs_executed.filter((r) => r.success).length;
        addNotification({
          type: "success",
          title: "Jonathan applied repairs",
          message: `${fixed} automated fix(es) completed on your system.`,
        });
      }
    } catch (err) {
      addNotification({
        type: "error",
        title: "Chat Error",
        message: String(err),
      });
    } finally {
      setLoading(false);
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
                ? "Cloud AI enabled — I diagnose, repair, and respond with GPT-powered summaries."
                : "Autonomous IT technician — I diagnose and repair issues for you automatically."}
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
              <span className="font-medium text-white">Cloud AI mode.</span> Repairs still run
              automatically on your device; responses are enhanced by your configured OpenAI model.
            </>
          ) : aiConfig?.enabled ? (
            <>
              <span className="font-medium text-warning">Cloud AI enabled but not active.</span> Add
              your API key in Settings → Jonathan AI (Cloud) and save to switch from autonomous
              mode.
            </>
          ) : (
            <>
              <span className="font-medium text-white">Autonomous repair mode.</span> Describe your
              issue and I&apos;ll run fixes automatically — no manual steps required. Works on the
              Free plan.
            </>
          )}
          {lastScan ? " Using your latest scan for context." : " Run a scan first for deeper fixes."}
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
                {msg.repairs && msg.repairs.length > 0 && !isTyping && (
                  <div className="mt-3 space-y-1 border-t border-navy-border/60 pt-2">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-steel">
                      Repairs executed
                    </p>
                    {msg.repairs.map((repair) => (
                      <p
                        key={repair.record_id}
                        className={`text-xs ${repair.success ? "text-success" : "text-warning"}`}
                      >
                        {repair.success ? "✓" : "⚠"} {repair.action_name || repair.message}
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
          <p className="mt-2 text-xs text-steel">
            Jonathan never requests passwords or credentials. All diagnostics require your consent.
          </p>
        </div>
      </div>
    </div>
  );
}
