import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-950 to-black text-white">
      <div className="mx-auto max-w-6xl px-6 py-24">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand-500">Thorpe Workforce</p>
        <h1 className="mt-4 max-w-3xl text-5xl font-semibold leading-tight">Hire AI employees that work 24/7.</h1>
        <p className="mt-6 max-w-3xl text-lg text-slate-300">
          Thorpe Workforce lets businesses deploy autonomous AI workers that find leads, generate outreach, follow up
          with prospects, and help book meetings automatically.
        </p>
        <div className="mt-10 flex gap-4">
          <Link href="/signup" className="btn-primary">
            Launch Your First AI Worker
          </Link>
          <Link href="/pricing" className="btn-secondary border-slate-700 bg-transparent text-white hover:bg-slate-800">
            View Pricing
          </Link>
          <Link href="/workers" className="btn-secondary border-slate-700 bg-transparent text-white hover:bg-slate-800">
            Browse Worker Library
          </Link>
        </div>
      </div>
    </main>
  );
}
