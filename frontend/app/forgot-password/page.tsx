"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { Mail, SendHorizonal } from "lucide-react";

import { AuthShell } from "@/components/layout/AuthShell";
import { ErrorState } from "@/components/ui/ErrorState";
import { api } from "@/services/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    try {
      setBusy(true);
      setError("");
      setMessage("");
      await api.post("/auth/forgot-password", { email });
      setMessage("If an account exists for that email, a reset link has been sent.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit request");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell title="Forgot password" subtitle="Enter your email and we’ll send a secure reset link immediately.">
      <form className="space-y-4" onSubmit={submit}>
        <div className="relative">
          <Mail className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <input
            className="w-full rounded-lg border border-slate-200 py-2 pl-9 pr-3"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        {error ? <ErrorState message={error} /> : null}
        {message ? <div className="card border-emerald-200/50 bg-emerald-950/20 p-3 text-sm text-emerald-200">{message}</div> : null}
        <button className="btn-primary w-full" disabled={busy}>
          {busy ? "Submitting..." : "Send Reset Link"}
          {!busy ? <SendHorizonal className="ml-1.5 h-4 w-4" /> : null}
        </button>
        <p className="text-sm text-slate-600">
          Back to{" "}
          <Link href="/login" className="text-brand-600 hover:underline">
            Login
          </Link>
        </p>
      </form>
    </AuthShell>
  );
}
