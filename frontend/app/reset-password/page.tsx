"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { KeyRound, RefreshCw } from "lucide-react";

import { AuthShell } from "@/components/layout/AuthShell";
import { ErrorState } from "@/components/ui/ErrorState";
import { api } from "@/services/api";

export default function ResetPasswordPage() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setToken(params.get("token") || "");
  }, []);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    try {
      setBusy(true);
      setError("");
      setMessage("");
      if (!token) {
        throw new Error("Reset token is missing.");
      }
      await api.post("/auth/reset-password", { token, new_password: newPassword });
      setMessage("Password updated successfully. Redirecting to login...");
      setTimeout(() => router.push("/login"), 1200);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reset password");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell title="Reset password" subtitle="Set a new password to regain secure access to your workspace.">
      <form className="space-y-4" onSubmit={submit}>
        <div className="relative">
          <KeyRound className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <input
            className="w-full rounded-lg border border-slate-200 py-2 pl-9 pr-3"
            type="password"
            placeholder="New password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            minLength={8}
          />
        </div>
        {error ? <ErrorState message={error} /> : null}
        {message ? <div className="card border-emerald-200/50 bg-emerald-950/20 p-3 text-sm text-emerald-200">{message}</div> : null}
        <button className="btn-primary w-full" disabled={busy}>
          {busy ? "Updating..." : "Update Password"}
          {!busy ? <RefreshCw className="ml-1.5 h-4 w-4" /> : null}
        </button>
        <p className="text-sm text-slate-600">
          Need a new reset link?{" "}
          <Link href="/forgot-password" className="text-brand-600 hover:underline">
            Request again
          </Link>
        </p>
      </form>
    </AuthShell>
  );
}
