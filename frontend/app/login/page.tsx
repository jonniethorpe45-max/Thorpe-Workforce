"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { ArrowRight } from "lucide-react";

import { AuthShell } from "@/components/layout/AuthShell";
import { ErrorState } from "@/components/ui/ErrorState";
import { login } from "@/services/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login({ email, password });
      router.push("/app/onboarding");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to log in");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell title="Log in to Thorpe Workforce" subtitle="Access your AI workers, missions, and automation control center.">
      <form className="space-y-4" onSubmit={submit}>
        <input
          className="w-full rounded-lg border border-slate-200 px-3 py-2"
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          className="w-full rounded-lg border border-slate-200 px-3 py-2"
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {error ? <ErrorState message={error} /> : null}
        <button className="btn-primary w-full" disabled={busy}>
          {busy ? "Logging in..." : "Log in"}
          {!busy ? <ArrowRight className="ml-1.5 h-4 w-4" /> : null}
        </button>
        <div className="space-y-2 text-sm text-slate-600">
          <p>
            Need an account?{" "}
            <Link href="/signup" className="text-brand-600 hover:underline">
              Sign up
            </Link>
          </p>
          <p>
            Forgot password?{" "}
            <Link href="/forgot-password" className="text-brand-600 hover:underline">
              Reset it
            </Link>
          </p>
        </div>
      </form>
    </AuthShell>
  );
}
