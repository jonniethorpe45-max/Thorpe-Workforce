import type { Metadata } from "next";

import { PublicFooter } from "@/components/layout/PublicFooter";
import { PublicNav } from "@/components/layout/PublicNav";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "Thorpe Workforce privacy policy and data handling overview."
};

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <PublicNav />
      <main className="mx-auto max-w-4xl space-y-5 px-6 py-12">
        <h1 className="text-3xl font-semibold text-slate-900">Privacy Policy</h1>
        <p className="text-sm text-slate-600">
          This policy explains how Thorpe Workforce collects, uses, and protects data across workspace operations,
          worker templates, and marketplace activity.
        </p>
        <section className="card p-5 text-sm text-slate-700">
          <h2 className="text-lg font-semibold">Data we collect</h2>
          <p className="mt-2">Account details, workspace configuration, usage analytics, billing metadata, and worker-generated output.</p>
          <h2 className="mt-4 text-lg font-semibold">How we use data</h2>
          <p className="mt-2">
            We use data to operate the platform, secure accounts, process billing, improve reliability, and enforce moderation policies.
          </p>
          <h2 className="mt-4 text-lg font-semibold">Marketplace and user-generated workers</h2>
          <p className="mt-2">
            Published workers and related metadata may be reviewed for trust and safety. We reserve the right to remove or hide content.
          </p>
          <h2 className="mt-4 text-lg font-semibold">Contact</h2>
          <p className="mt-2">For privacy requests, contact support@thorpeworkforce.com.</p>
        </section>
      </main>
      <PublicFooter />
    </div>
  );
}
