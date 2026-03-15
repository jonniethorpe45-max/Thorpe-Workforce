import type { Metadata } from "next";

import { PublicFooter } from "@/components/layout/PublicFooter";
import { PublicNav } from "@/components/layout/PublicNav";

export const metadata: Metadata = {
  title: "About",
  description: "Learn about Thorpe Workforce and our AI worker platform mission."
};

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <PublicNav />
      <main className="mx-auto max-w-4xl space-y-4 px-6 py-12">
        <h1 className="text-3xl font-semibold text-slate-900">About Thorpe Workforce</h1>
        <p className="text-slate-700">
          Thorpe Workforce helps teams deploy AI workers that execute repeatable business tasks with clear controls,
          run history, approvals, and operational analytics.
        </p>
        <section className="card p-5">
          <h2 className="text-xl font-semibold">Our mission</h2>
          <p className="mt-2 text-sm text-slate-600">
            Make AI execution practical for real operators by combining worker templates, secure workflows, and
            monetizable marketplace distribution.
          </p>
        </section>
      </main>
      <PublicFooter />
    </div>
  );
}
