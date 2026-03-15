import Link from "next/link";
import type { Metadata } from "next";
import { ArrowRight, Bot, ChartSpline, Crown, Cpu, Sparkles, Store, Workflow } from "lucide-react";

import { PublicFooter } from "@/components/layout/PublicFooter";
import { PublicNav } from "@/components/layout/PublicNav";

export const metadata: Metadata = {
  title: "AI Worker Platform",
  description: "Build, deploy, and monetize AI workers with Thorpe Workforce."
};

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-900">
      <PublicNav />
      <main>
        <section className="relative overflow-hidden border-b border-slate-200/40">
          <div className="mx-auto grid max-w-6xl gap-10 px-6 py-20 lg:grid-cols-[1.15fr_0.85fr]">
            <div>
              <p className="inline-flex items-center gap-1 rounded-full border border-cyan-400/35 bg-cyan-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-cyan-200">
                <Sparkles className="h-3.5 w-3.5" />
                AI Command Center
              </p>
              <h1 className="mt-5 max-w-4xl bg-gradient-to-r from-slate-100 via-cyan-100 to-indigo-300 bg-clip-text text-5xl font-semibold leading-tight text-transparent">
                Deploy AI workers to run your business.
              </h1>
              <p className="mt-6 max-w-3xl text-lg text-slate-600">
                Thorpe Workforce is an AI worker platform where digital workers automate tasks, analyze data, and accelerate
                productivity across sales, operations, and growth.
              </p>
              <div className="mt-10 flex flex-wrap gap-3">
                <Link href="/signup" className="btn-primary">
                  Launch your first worker
                  <ArrowRight className="ml-1.5 h-4 w-4" />
                </Link>
                <Link href="/marketplace" className="btn-secondary">
                  Explore marketplace
                </Link>
                <Link href="/pricing" className="btn-secondary">
                  View pricing
                </Link>
              </div>
            </div>
            <div className="card p-6">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Live platform snapshot</p>
              <div className="mt-4 space-y-3">
                {[
                  { label: "Active workers", value: "42", Icon: Cpu },
                  { label: "Automations running", value: "18", Icon: Workflow },
                  { label: "Founder reports generated", value: "129", Icon: Crown },
                  { label: "Marketplace templates", value: "300+", Icon: Store }
                ].map(({ label, value, Icon }) => (
                  <div key={label} className="flex items-center justify-between rounded-xl border border-slate-200/50 bg-slate-900/60 px-3 py-2.5">
                    <div className="flex items-center gap-2">
                      <span className="rounded-md border border-cyan-400/30 bg-cyan-400/10 p-1.5 text-cyan-300">
                        <Icon className="h-3.5 w-3.5" />
                      </span>
                      <span className="text-sm text-slate-600">{label}</span>
                    </div>
                    <span className="text-sm font-semibold text-slate-900">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 py-14">
          <h2 className="section-title">How it works</h2>
          <p className="section-subtitle">From mission definition to run execution and analytics insight.</p>
          <div className="mt-5 grid gap-4 md:grid-cols-4">
            {[
              { title: "Choose a mission", body: "Define business outcomes and deploy the right worker stack.", Icon: Bot },
              { title: "Install or build", body: "Use marketplace templates or create custom workers in Builder.", Icon: Store },
              { title: "Execute runs", body: "Launch workers manually or schedule repeatable chain automations.", Icon: Workflow },
              { title: "Analyze and optimize", body: "Track performance dashboards and iterate with data.", Icon: ChartSpline }
            ].map(({ title, body, Icon }) => (
              <article key={title} className="card p-4">
                <span className="mb-3 inline-flex rounded-lg border border-indigo-400/35 bg-indigo-400/10 p-2 text-indigo-300">
                  <Icon className="h-4 w-4" />
                </span>
                <h3 className="font-semibold">{title}</h3>
                <p className="mt-2 text-sm text-slate-600">{body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 pb-12">
          <h2 className="section-title">Marketplace + creator ecosystem</h2>
          <p className="section-subtitle">Discover, install, and monetize workers in a unified AI operating system.</p>
          <div className="mt-5 grid gap-4 md:grid-cols-3">
            {[
              ["Featured workers", "Surface top performers with ratings, installs, and category fit."],
              ["Creator analytics", "Monitor installs, usage, and revenue estimates from one dashboard."],
              ["Founder OS chains", "Orchestrate multi-worker workflows for daily business operations."]
            ].map(([title, body]) => (
              <article key={title} className="card p-4">
                <h3 className="font-semibold">{title}</h3>
                <p className="mt-2 text-sm text-slate-600">{body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 pb-12">
          <h2 className="section-title">Why Thorpe Workforce</h2>
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
                <ArrowRight className="ml-1.5 h-4 w-4" />
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
