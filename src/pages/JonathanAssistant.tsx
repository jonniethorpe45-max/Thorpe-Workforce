import { useEffect, useRef, useState } from "react";
import { Send, User, Sparkles, Mic } from "lucide-react";
import { motion } from "framer-motion";
import { thorpeApi } from "../services/tauri";
import { useAppStore } from "../services/store";
import { JONATHAN_WELCOME } from "../prompts/jonathan";
import { JonathanAvatar } from "../components/brand/JonathanAvatar";
import { SafeMarkdown } from "../components/ui/SafeMarkdown";

interface Message {
  role: "user" | "assistant";
  content: string;
  source?: string;
}

export function JonathanAssistant() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: JONATHAN_WELCOME },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [skillLevel, setSkillLevel] = useState("beginner");
  const { lastScan, addNotification } = useAppStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    thorpeApi.getProfile().then((p) => setSkillLevel(p.skill_level)).catch(console.error);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.message, source: response.source },
      ]);
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

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col animate-fade-in">
      <div className="card-brand mb-4 flex items-center justify-between gap-4 p-4">
        <div className="flex items-center gap-4">
          <JonathanAvatar size="md" />
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-thorpe-primary">
              AI Technician
            </p>
            <h1 className="font-display text-xl font-bold text-white">Jonathan</h1>
            <p className="text-sm text-steel">
              &ldquo;Hi, I&apos;m Jonathan. I&apos;m here to help you understand and fix your
              technology.&rdquo;
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

      <div className="card flex flex-1 flex-col overflow-hidden p-0">
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.map((msg, i) => (
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
                  <SafeMarkdown content={msg.content} />
                )}
                {msg.source && msg.role === "assistant" && (
                  <p className="mt-2 flex items-center gap-1 text-xs text-steel">
                    <Sparkles className="h-3 w-3 text-cyber-teal" />
                    {msg.source === "openai" ? "Cloud AI" : "Local guidance"}
                  </p>
                )}
              </div>
            </motion.div>
          ))}
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
