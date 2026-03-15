import type { Metadata } from "next";

import { PublicFooter } from "@/components/layout/PublicFooter";
import { PublicNav } from "@/components/layout/PublicNav";

export const metadata: Metadata = {
  title: "Acceptable Use Policy",
  description: "Rules for responsible and compliant use of Thorpe Workforce."
};

export default function AcceptableUsePage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <PublicNav />
      <main className="mx-auto max-w-4xl space-y-5 px-6 py-12">
        <h1 className="text-3xl font-semibold text-slate-900">Acceptable Use Policy</h1>
        <section className="card space-y-3 p-5 text-sm text-slate-700">
          <p>Thorpe Workforce is intended for legitimate business workflows and responsible AI automation.</p>
          <h2 className="text-lg font-semibold">Prohibited activities</h2>
          <ul className="list-disc space-y-1 pl-5">
            <li>Spam, phishing, or deceptive outreach.</li>
            <li>Automated harassment, abuse, or discriminatory targeting.</li>
            <li>Malware, credential theft, or unauthorized system access.</li>
            <li>Publishing workers that violate laws, privacy rights, or IP rights.</li>
          </ul>
          <h2 className="text-lg font-semibold">Enforcement</h2>
          <p>
            We may suspend workspaces, hide marketplace workers, revoke access, or report abuse when policy violations
            are identified.
          </p>
        </section>
      </main>
      <PublicFooter />
    </div>
  );
}
