import Link from "next/link";
import { ScoutWorkspace } from "@/components/ScoutWorkspace";

export default function HomePage() {
  return (
    <main className="relative overflow-hidden">
      <section className="relative min-h-[100svh] bg-terrain">
        <div className="pointer-events-none absolute inset-0 animate-drift">
          <div className="map-grid absolute inset-0" />
          <svg
            className="absolute inset-0 h-full w-full opacity-40"
            viewBox="0 0 1200 800"
            preserveAspectRatio="xMidYMid slice"
            aria-hidden
          >
            <path
              className="animate-pulse-line"
              d="M80 620 C220 520, 280 400, 420 380 S680 420, 760 300 S980 180, 1120 220"
              fill="none"
              stroke="#d6f26a"
              strokeWidth="1.5"
              strokeOpacity="0.55"
            />
            <path
              d="M40 240 C180 260, 260 320, 360 280 S560 140, 700 180 S920 320, 1160 260"
              fill="none"
              stroke="#6f9b7a"
              strokeWidth="1"
              strokeOpacity="0.45"
            />
            <circle cx="760" cy="300" r="6" fill="#d6f26a" fillOpacity="0.9" />
            <circle cx="420" cy="380" r="4" fill="#e8efe6" fillOpacity="0.7" />
          </svg>
        </div>

        <div className="relative z-10 mx-auto flex min-h-[100svh] max-w-6xl flex-col px-6 pb-16 pt-8">
          <header className="flex items-center justify-between">
            <p className="font-display text-3xl tracking-tight text-parchment md:text-4xl">
              ScoutAI
            </p>
            <Link
              href="#scout"
              className="rounded-sm border border-white/15 px-3 py-1.5 text-sm text-moss-300 transition hover:border-signal/50 hover:text-parchment"
            >
              Open workspace
            </Link>
          </header>

          <div className="mt-auto max-w-3xl pb-10 pt-24">
            <h1 className="animate-rise font-display text-5xl leading-[1.05] tracking-tight text-parchment md:text-7xl">
              Research that finds the signal.
            </h1>
            <p className="animate-rise-delay-1 mt-6 max-w-xl text-lg text-moss-300 md:text-xl">
              Point ScoutAI at a topic, market, or competitor. Get a sourced intelligence
              brief with findings, risks, and next moves.
            </p>
            <div className="animate-rise-delay-2 mt-8 flex flex-wrap gap-3">
              <Link
                href="#scout"
                className="rounded-sm bg-signal px-5 py-2.5 text-sm font-semibold text-ink-950 transition hover:bg-signal-soft"
              >
                Start a scout
              </Link>
              <a
                href="https://github.com/jonniethorpe45-max"
                className="rounded-sm border border-white/15 px-5 py-2.5 text-sm text-moss-300 transition hover:border-signal/40 hover:text-parchment"
              >
                View portfolio
              </a>
            </div>
          </div>
        </div>
      </section>

      <div className="animate-rise-delay-3 bg-ink-900/40">
        <ScoutWorkspace />
      </div>

      <footer className="border-t border-white/10 px-6 py-8 text-center text-sm text-moss-400">
        ScoutAI · intelligence briefs for builders
      </footer>
    </main>
  );
}
