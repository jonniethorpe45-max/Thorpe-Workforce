"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { signup } from "@/services/auth";

export default function SignupPage() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    company_name: "",
    website: "",
    industry: ""
  });

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await signup(form);
      router.push("/app");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign up");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-lg items-center px-6">
      <form className="card w-full space-y-4 p-6" onSubmit={submit}>
        <h1 className="text-2xl font-semibold">Create your Thorpe Workforce workspace</h1>
        <input
          className="w-full rounded-lg border border-slate-200 px-3 py-2"
          placeholder="Full name"
          value={form.full_name}
          onChange={(e) => setForm((s) => ({ ...s, full_name: e.target.value }))}
          required
        />
        <input
          className="w-full rounded-lg border border-slate-200 px-3 py-2"
          type="email"
          placeholder="Work email"
          value={form.email}
          onChange={(e) => setForm((s) => ({ ...s, email: e.target.value }))}
          required
        />
        <input
          className="w-full rounded-lg border border-slate-200 px-3 py-2"
          type="password"
          placeholder="Password"
          value={form.password}
          onChange={(e) => setForm((s) => ({ ...s, password: e.target.value }))}
          required
        />
        <input
          className="w-full rounded-lg border border-slate-200 px-3 py-2"
          placeholder="Company name"
          value={form.company_name}
          onChange={(e) => setForm((s) => ({ ...s, company_name: e.target.value }))}
          required
        />
        <input
          className="w-full rounded-lg border border-slate-200 px-3 py-2"
          placeholder="Website"
          value={form.website}
          onChange={(e) => setForm((s) => ({ ...s, website: e.target.value }))}
        />
        <input
          className="w-full rounded-lg border border-slate-200 px-3 py-2"
          placeholder="Industry"
          value={form.industry}
          onChange={(e) => setForm((s) => ({ ...s, industry: e.target.value }))}
        />
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        <button className="btn-primary w-full" disabled={busy}>
          {busy ? "Creating..." : "Launch Your First AI Worker"}
        </button>
        <p className="text-sm text-slate-600">
          Already have an account?{" "}
          <Link href="/login" className="text-brand-600 hover:underline">
            Log in
          </Link>
        </p>
      </form>
    </main>
  );
}
