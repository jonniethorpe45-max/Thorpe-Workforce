"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

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
      router.push("/app");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to log in");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-md items-center px-6">
      <form className="card w-full space-y-4 p-6" onSubmit={submit}>
        <h1 className="text-2xl font-semibold">Log in to Thorpe Workforce</h1>
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
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        <button className="btn-primary w-full" disabled={busy}>
          {busy ? "Logging in..." : "Log in"}
        </button>
        <p className="text-sm text-slate-600">
          Need an account?{" "}
          <Link href="/signup" className="text-brand-600 hover:underline">
            Sign up
          </Link>
        </p>
      </form>
    </main>
  );
}
