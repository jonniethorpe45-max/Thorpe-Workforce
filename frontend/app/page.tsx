import Link from "next/link";
import type { Metadata } from "next";

import { PublicFooter } from "@/components/layout/PublicFooter";
import { PublicNav } from "@/components/layout/PublicNav";

export const metadata: Metadata = {
  title: "AI Worker Platform",
  description: "Build, deploy, and monetize AI workers with Thorpe Workforce."
};

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <PublicNav />
      <main>
        <section className="bg-gradient-to-b from-slate-900 via-slate-950 to-black text-white">
          <div className="mx-auto max-w-6xl px-6 py-20">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand-500">Thorpe Workforce</p>
            <h1 className="mt-4 max-w-4xl text-5xl font-semibold leading-tight">
              Deploy AI workers that run missions, generate output, and deliver outcomes.
            </h1>
            <p className="mt-6 max-w-3xl text-lg text-slate-300">
              Thorpe Workforce is the AI Worker Platform for teams that want execution, not chat tabs. Build workers,
              install marketplace workers, run them on repeat, and monetize your own templates.
            </p>
            <div className="mt-10 flex flex-wrap gap-3">
              <Link href="/signup" className="btn-primary">
                Launch your first worker
              </Link>
              <Link href="/marketplace" className="btn-secondary border-slate-700 bg-transparent text-white hover:bg-slate-800">
                Explore marketplace
              </Link>
              <Link href="/pricing" className="btn-secondary border-slate-700 bg-transparent text-white hover:bg-slate-800">
                View pricing
              </Link>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 py-14">
          <h2 className="text-2xl font-semibold">How it works</h2>
          <div className="mt-5 grid gap-4 md:grid-cols-4">
            {[
              ["Choose a goal", "Sales, marketing, research, operations, and more."],
              ["Install or build", "Use starter workers or create custom workers in the builder."],
              ["Run worker missions", "Execute runs manually or as recurring workflows."],
              ["Measure and scale", "Track analytics, optimize output, and upgrade as you grow."]
            ].map(([title, body]) => (
              <article key={title} className="card p-4">
                <h3 className="font-semibold">{title}</h3>
                <p className="mt-2 text-sm text-slate-600">{body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 pb-12">
          <h2 className="text-2xl font-semibold">Why Thorpe Workforce</h2>
          <div className="mt-5 grid gap-4 md:grid-cols-3">
            <article className="card p-4">
              <h3 className="font-semibold">Worker-native execution</h3>
              <p className="mt-2 text-sm text-slate-600">
                Structured worker templates, run history, approval queues, and production-style operations controls.
              </p>
            </article>
            <article className="card p-4">
              <h3 className="font-semibold">Creator economy built in</h3>
              <p className="mt-2 text-sm text-slate-600">
                Publish marketplace workers, track installs and analytics, and build monetizable AI worker products.
              </p>
            </article>
            <article className="card p-4">
              <h3 className="font-semibold">Operator-grade controls</h3>
              <p className="mt-2 text-sm text-slate-600">
                Entitlements, moderation, analytics, and admin visibility are built into the platform core.
              </p>
            </article>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 pb-16">
          <div className="card flex flex-col gap-4 p-6 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-2xl font-semibold">Ready to launch your AI workforce?</h2>
              <p className="mt-2 text-sm text-slate-600">
                Start free, run your first worker in minutes, and upgrade when your team scales.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link className="btn-primary" href="/signup">
                Get Started
              </Link>
              <Link className="btn-secondary" href="/pricing">
                Compare Plans
              </Link>
            </div>
          </div>
        </section>
      </main>
      <PublicFooter />
    </div>
  );
}
