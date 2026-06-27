import { useEffect, useRef, useState } from "react";
import { Send, Bot, User, Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import { thorpeApi } from "../services/tauri";
import { useAppStore } from "../services/store";
import { JONATHAN_WELCOME } from "../prompts/jonathan";

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

  const formatContent = (content: string) => {
    return content.split("\n").map((line, i) => {
      const formatted = line
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.*?)\*/g, "<em>$1</em>");
      return (
        <span key={i}>
          <span dangerouslySetInnerHTML={{ __html: formatted }} />
          {i < content.split("\n").length - 1 && <br />}
        </span>
      );
    });
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col animate-fade-in">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-thorpe-600/20">
            <Bot className="h-5 w-5 text-thorpe-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Jonathan</h1>
            <p className="text-sm text-gray-400">Your AI IT Technician</p>
          </div>
        </div>
        <select
          value={skillLevel}
          onChange={(e) => setSkillLevel(e.target.value)}
          className="input w-auto text-sm"
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
              <div
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                  msg.role === "user" ? "bg-surface-overlay" : "bg-thorpe-600/20"
                }`}
              >
                {msg.role === "user" ? (
                  <User className="h-4 w-4 text-gray-400" />
                ) : (
                  <Bot className="h-4 w-4 text-thorpe-400" />
                )}
              </div>
              <div
                className={`max-w-[75%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-thorpe-600 text-white"
                    : "bg-surface text-gray-200"
                }`}
              >
                {formatContent(msg.content)}
                {msg.source && msg.role === "assistant" && (
                  <p className="mt-2 flex items-center gap-1 text-xs text-gray-500">
                    <Sparkles className="h-3 w-3" />
                    {msg.source === "openai" ? "Cloud AI" : "Local guidance"}
                  </p>
                )}
              </div>
            </motion.div>
          ))}
          {loading && (
            <div className="flex gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-thorpe-600/20">
                <Bot className="h-4 w-4 text-thorpe-400" />
              </div>
              <div className="rounded-xl bg-surface px-4 py-3">
                <div className="flex gap-1">
                  <span className="h-2 w-2 animate-pulse rounded-full bg-thorpe-400" />
                  <span className="h-2 w-2 animate-pulse rounded-full bg-thorpe-400 [animation-delay:0.2s]" />
                  <span className="h-2 w-2 animate-pulse rounded-full bg-thorpe-400 [animation-delay:0.4s]" />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="border-t border-surface-border p-4">
          <div className="flex gap-3">
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
          <p className="mt-2 text-xs text-gray-500">
            Jonathan never requests passwords or credentials. All diagnostics require your consent.
          </p>
        </div>
      </div>
    </div>
  );
}
