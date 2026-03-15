"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { Rocket } from "lucide-react";

import { AuthShell } from "@/components/layout/AuthShell";
import { ErrorState } from "@/components/ui/ErrorState";
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
      router.push("/app/onboarding");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign up");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell
      title="Create your Thorpe Workforce workspace"
      subtitle="Deploy your first AI worker in minutes and activate mission-driven automations."
      maxWidthClassName="max-w-4xl"
    >
      <form className="space-y-4" onSubmit={submit}>
        <div className="grid gap-3 md:grid-cols-2">
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
        </div>
        {error ? <ErrorState message={error} /> : null}
        <button className="btn-primary w-full" disabled={busy}>
          {busy ? "Creating..." : "Launch Your First AI Worker"}
          {!busy ? <Rocket className="ml-1.5 h-4 w-4" /> : null}
        </button>
        <p className="text-sm text-slate-600">
          Already have an account?{" "}
          <Link href="/login" className="text-brand-600 hover:underline">
            Log in
          </Link>
        </p>
      </form>
    </AuthShell>
  );
}
