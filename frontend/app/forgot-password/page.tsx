"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { PublicFooter } from "@/components/layout/PublicFooter";
import { PublicNav } from "@/components/layout/PublicNav";
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
    <div className="min-h-screen bg-slate-50">
      <PublicNav />
      <main className="mx-auto flex min-h-[calc(100vh-180px)] max-w-md items-center px-6">
        <form className="card w-full space-y-4 p-6" onSubmit={submit}>
          <h1 className="text-2xl font-semibold">Forgot Password</h1>
          <p className="text-sm text-slate-600">Enter your email and we’ll send a password reset link.</p>
          <input
            className="w-full rounded-lg border border-slate-200 px-3 py-2"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          {error ? <p className="text-sm text-rose-600">{error}</p> : null}
          {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
          <button className="btn-primary w-full" disabled={busy}>
            {busy ? "Submitting..." : "Send Reset Link"}
          </button>
          <p className="text-sm text-slate-600">
            Back to{" "}
            <Link href="/login" className="text-brand-600 hover:underline">
              Login
            </Link>
          </p>
        </form>
      </main>
      <PublicFooter />
    </div>
  );
}
