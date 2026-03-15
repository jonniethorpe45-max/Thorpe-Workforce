import type { Metadata } from "next";

import { PublicFooter } from "@/components/layout/PublicFooter";
import { PublicNav } from "@/components/layout/PublicNav";

export const metadata: Metadata = {
  title: "Terms of Service",
  description: "Thorpe Workforce terms governing account, billing, and marketplace usage."
};

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <PublicNav />
      <main className="mx-auto max-w-4xl space-y-5 px-6 py-12">
        <h1 className="text-3xl font-semibold text-slate-900">Terms of Service</h1>
        <section className="card space-y-3 p-5 text-sm text-slate-700">
          <p>
            These Terms govern access to Thorpe Workforce, including account use, subscriptions, marketplace
            participation, and worker publishing rights.
          </p>
          <h2 className="text-lg font-semibold">Accounts and billing</h2>
          <p>Customers are responsible for account security, payment obligations, and maintaining valid billing details.</p>
          <h2 className="text-lg font-semibold">Worker content and moderation</h2>
          <p>
            Creators are responsible for worker content they publish. We may moderate, reject, or remove workers that
            violate policy or create safety/compliance risks.
          </p>
          <h2 className="text-lg font-semibold">Acceptable use</h2>
          <p>
            You may not use the platform for abusive, deceptive, unlawful, or harmful automation, including spam,
            phishing, malware distribution, or rights violations.
          </p>
          <h2 className="text-lg font-semibold">Liability</h2>
          <p>Service is provided as-is during launch; customers should review outputs before business-critical use.</p>
        </section>
      </main>
      <PublicFooter />
    </div>
  );
}
