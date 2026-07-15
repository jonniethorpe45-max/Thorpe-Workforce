"use client";

import { FormEvent, useState } from "react";
import { ResearchBrief, runResearch } from "@/lib/api";

const FOCUSES = [
  { id: "general", label: "General" },
  { id: "market", label: "Market" },
  { id: "competitor", label: "Competitor" },
  { id: "product", label: "Product" },
] as const;

type Focus = (typeof FOCUSES)[number]["id"];

export function ScoutWorkspace() {
  const [query, setQuery] = useState("");
  const [focus, setFocus] = useState<Focus>("general");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [brief, setBrief] = useState<ResearchBrief | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!query.trim() || loading) return;
    setLoading(true);
    setError(null);
    try {
      const result = await runResearch({ query: query.trim(), focus, depth: "standard" });
      setBrief(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scout run failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section id="scout" className="relative mx-auto max-w-5xl px-6 pb-24 pt-8">
      <div className="mb-8 max-w-2xl">
        <h2 className="font-display text-4xl tracking-tight text-parchment md:text-5xl">
          Scout workspace
        </h2>
        <p className="mt-3 text-moss-300">
          One question in. A structured brief out — findings, risks, and next actions.
        </p>
      </div>

      <form onSubmit={onSubmit} className="space-y-5">
        <label className="block">
          <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-moss-400">
            What should Scout investigate?
          </span>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            rows={4}
            placeholder="e.g. Competitive landscape for AI receptionist products targeting dental clinics"
            className="w-full resize-y rounded-sm border border-white/10 bg-ink-900/80 px-4 py-3 text-parchment outline-none ring-signal/40 transition focus:ring-2"
          />
        </label>

        <div className="flex flex-wrap items-center gap-2">
          {FOCUSES.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setFocus(item.id)}
              className={`rounded-sm px-3 py-1.5 text-sm transition ${
                focus === item.id
                  ? "bg-signal text-ink-950"
                  : "border border-white/10 text-moss-300 hover:border-signal/40 hover:text-parchment"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>

        <button
          type="submit"
          disabled={loading || query.trim().length < 3}
          className="inline-flex items-center gap-2 rounded-sm bg-signal px-5 py-2.5 text-sm font-semibold text-ink-950 transition hover:bg-signal-soft disabled:cursor-not-allowed disabled:opacity-40"
        >
          {loading ? "Scouting…" : "Run scout"}
          <span aria-hidden>→</span>
        </button>
      </form>

      {error && (
        <p className="mt-6 border-l-2 border-red-400/70 pl-3 text-sm text-red-200">{error}</p>
      )}

      {brief && (
        <article className="mt-12 space-y-8 border-t border-white/10 pt-10">
          <header className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-moss-400">
                Brief · {brief.mode} mode · {brief.focus}
              </p>
              <h3 className="mt-2 font-display text-3xl text-parchment">{brief.query}</h3>
            </div>
          </header>

          <p className="max-w-3xl text-lg leading-relaxed text-parchment/90">{brief.summary}</p>

          <div className="space-y-5">
            <h4 className="text-xs font-semibold uppercase tracking-[0.18em] text-signal">
              Findings
            </h4>
            <ul className="space-y-5">
              {brief.findings.map((finding) => (
                <li key={finding.title} className="border-l border-signal/40 pl-4">
                  <p className="font-semibold text-parchment">{finding.title}</p>
                  <p className="mt-1 text-moss-300">{finding.detail}</p>
                  <p className="mt-2 text-xs uppercase tracking-wider text-moss-400">
                    Confidence · {finding.confidence}
                  </p>
                </li>
              ))}
            </ul>
          </div>

          <div className="grid gap-8 md:grid-cols-2">
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-[0.18em] text-signal">
                Risks
              </h4>
              <ul className="mt-3 space-y-2 text-moss-300">
                {brief.risks.map((risk) => (
                  <li key={risk}>· {risk}</li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-[0.18em] text-signal">
                Next actions
              </h4>
              <ul className="mt-3 space-y-2 text-moss-300">
                {brief.next_actions.map((action) => (
                  <li key={action}>· {action}</li>
                ))}
              </ul>
            </div>
          </div>

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-[0.18em] text-signal">
              Sources
            </h4>
            <ul className="mt-3 space-y-2 text-sm text-moss-300">
              {brief.sources.map((source) => (
                <li key={source.title}>
                  {source.url ? (
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-signal-soft underline-offset-2 hover:underline"
                    >
                      {source.title}
                    </a>
                  ) : (
                    source.title
                  )}
                  {source.note ? ` — ${source.note}` : null}
                </li>
              ))}
            </ul>
          </div>
        </article>
      )}
    </section>
  );
}
