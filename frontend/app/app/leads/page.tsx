"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { TableShell } from "@/components/tables/TableShell";
import { api } from "@/services/api";
import type { Campaign, Lead } from "@/types";

type LeadCreatePayload = {
  campaign_id?: string;
  company_name: string;
  full_name?: string;
  title?: string;
  email: string;
};

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[] | null>(null);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState<LeadCreatePayload>({
    company_name: "",
    full_name: "",
    title: "",
    email: ""
  });

  const load = async () => {
    const [leadData, campaignData] = await Promise.all([api.get<Lead[]>("/leads"), api.get<Campaign[]>("/campaigns")]);
    setLeads(leadData);
    setCampaigns(campaignData);
  };

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load leads"));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!leads) return <LoadingState label="Loading leads..." />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post("/leads", form);
      setForm({ company_name: "", full_name: "", title: "", email: "", campaign_id: form.campaign_id });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add lead");
    } finally {
      setBusy(false);
    }
  };

  if (!leads.length) {
    return (
      <div className="space-y-4">
        <form className="card grid gap-3 p-4 md:grid-cols-5" onSubmit={submit}>
          <input
            className="rounded-lg border border-slate-200 px-3 py-2"
            placeholder="Company name"
            value={form.company_name}
            onChange={(e) => setForm((s) => ({ ...s, company_name: e.target.value }))}
            required
          />
          <input
            className="rounded-lg border border-slate-200 px-3 py-2"
            placeholder="Contact name"
            value={form.full_name}
            onChange={(e) => setForm((s) => ({ ...s, full_name: e.target.value }))}
          />
          <input
            className="rounded-lg border border-slate-200 px-3 py-2"
            placeholder="Title"
            value={form.title}
            onChange={(e) => setForm((s) => ({ ...s, title: e.target.value }))}
          />
          <input
            className="rounded-lg border border-slate-200 px-3 py-2"
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={(e) => setForm((s) => ({ ...s, email: e.target.value }))}
            required
          />
          <button className="btn-primary" disabled={busy}>
            {busy ? "Adding..." : "Add Lead"}
          </button>
        </form>
        <EmptyState title="No leads yet" description="Add your first lead to start worker research and drafting." />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="section-title">Leads</h2>
      <form className="card grid gap-3 p-4 md:grid-cols-6" onSubmit={submit}>
        <input
          className="rounded-lg border border-slate-200 px-3 py-2"
          placeholder="Company"
          value={form.company_name}
          onChange={(e) => setForm((s) => ({ ...s, company_name: e.target.value }))}
          required
        />
        <input
          className="rounded-lg border border-slate-200 px-3 py-2"
          placeholder="Contact name"
          value={form.full_name}
          onChange={(e) => setForm((s) => ({ ...s, full_name: e.target.value }))}
        />
        <input
          className="rounded-lg border border-slate-200 px-3 py-2"
          placeholder="Title"
          value={form.title}
          onChange={(e) => setForm((s) => ({ ...s, title: e.target.value }))}
        />
        <input
          className="rounded-lg border border-slate-200 px-3 py-2"
          type="email"
          placeholder="Email"
          value={form.email}
          onChange={(e) => setForm((s) => ({ ...s, email: e.target.value }))}
          required
        />
        <select
          className="rounded-lg border border-slate-200 px-3 py-2"
          value={form.campaign_id || ""}
          onChange={(e) => setForm((s) => ({ ...s, campaign_id: e.target.value || undefined }))}
        >
          <option value="">Mission (optional)</option>
          {campaigns.map((campaign) => (
            <option key={campaign.id} value={campaign.id}>
              {campaign.name}
            </option>
          ))}
        </select>
        <button className="btn-primary" disabled={busy}>
          {busy ? "Adding..." : "Add Lead"}
        </button>
      </form>
      <TableShell>
        <div className="border-b border-slate-200/60 px-4 py-3 text-sm text-slate-500">Lead pipeline</div>
        <table className="min-w-full text-sm">
          <thead className="text-left text-slate-600">
            <tr>
              <th className="px-4 py-3">Lead</th>
              <th className="px-4 py-3">Company</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((lead) => (
              <tr key={lead.id} className="border-t border-slate-200">
                <td className="px-4 py-3">
                  <Link href={`/app/leads/${lead.id}`} className="font-medium text-brand-600 hover:underline">
                    {lead.full_name || lead.email}
                  </Link>
                </td>
                <td className="px-4 py-3">{lead.company_name}</td>
                <td className="px-4 py-3">{lead.email}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={lead.lead_status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableShell>
    </div>
  );
}
