"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { PublicFooter } from "@/components/layout/PublicFooter";
import { PublicNav } from "@/components/layout/PublicNav";
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
    <div className="min-h-screen bg-slate-50">
      <PublicNav />
      <main className="mx-auto flex min-h-[calc(100vh-180px)] max-w-md items-center px-6">
        <form className="card w-full space-y-4 p-6" onSubmit={submit}>
          <h1 className="text-2xl font-semibold">Reset Password</h1>
          <p className="text-sm text-slate-600">Choose a new password for your Thorpe Workforce account.</p>
          <input
            className="w-full rounded-lg border border-slate-200 px-3 py-2"
            type="password"
            placeholder="New password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            minLength={8}
          />
          {error ? <p className="text-sm text-rose-600">{error}</p> : null}
          {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
          <button className="btn-primary w-full" disabled={busy}>
            {busy ? "Updating..." : "Update Password"}
          </button>
          <p className="text-sm text-slate-600">
            Need a new reset link?{" "}
            <Link href="/forgot-password" className="text-brand-600 hover:underline">
              Request again
            </Link>
          </p>
        </form>
      </main>
      <PublicFooter />
    </div>
  );
}
