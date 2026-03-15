"use client";

import { FormEvent, useState } from "react";

import { PublicFooter } from "@/components/layout/PublicFooter";
import { PublicNav } from "@/components/layout/PublicNav";
import { api } from "@/services/api";

export default function ContactPage() {
  const [form, setForm] = useState({ name: "", email: "", subject: "", message: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    try {
      setBusy(true);
      setError("");
      setSuccess("");
      await api.post("/support/contact", {
        name: form.name,
        email: form.email,
        subject: form.subject,
        message: form.message,
        source: "public_contact_page"
      });
      setSuccess("Thanks — your message has been received. Our team will follow up shortly.");
      setForm({ name: "", email: "", subject: "", message: "" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit contact request");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <PublicNav />
      <main className="mx-auto max-w-2xl space-y-4 px-6 py-12">
        <h1 className="text-3xl font-semibold text-slate-900">Contact Thorpe Workforce</h1>
        <p className="text-sm text-slate-600">Questions about launch, support, billing, or enterprise use? Reach out below.</p>
        <form className="card space-y-3 p-5" onSubmit={submit}>
          <input
            className="w-full rounded-lg border border-slate-200 px-3 py-2"
            placeholder="Name"
            value={form.name}
            onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
            required
          />
          <input
            className="w-full rounded-lg border border-slate-200 px-3 py-2"
            placeholder="Email"
            type="email"
            value={form.email}
            onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))}
            required
          />
          <input
            className="w-full rounded-lg border border-slate-200 px-3 py-2"
            placeholder="Subject"
            value={form.subject}
            onChange={(e) => setForm((prev) => ({ ...prev, subject: e.target.value }))}
            required
          />
          <textarea
            className="h-36 w-full rounded-lg border border-slate-200 px-3 py-2"
            placeholder="How can we help?"
            value={form.message}
            onChange={(e) => setForm((prev) => ({ ...prev, message: e.target.value }))}
            required
          />
          {error ? <p className="text-sm text-rose-600">{error}</p> : null}
          {success ? <p className="text-sm text-emerald-700">{success}</p> : null}
          <button className="btn-primary" disabled={busy}>
            {busy ? "Sending..." : "Send Message"}
          </button>
        </form>
      </main>
      <PublicFooter />
    </div>
  );
}
