import Link from "next/link";
import { BrainCircuit, Sparkles } from "lucide-react";

export function PublicNav() {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/60 bg-slate-950/75 backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="inline-flex items-center gap-2 text-lg font-semibold text-slate-100">
          <span className="rounded-lg border border-cyan-400/35 bg-cyan-400/10 p-1.5 text-cyan-300">
            <BrainCircuit className="h-4 w-4" />
          </span>
          Thorpe Workforce
        </Link>
        <nav className="hidden items-center gap-5 text-sm text-slate-700 md:flex">
          <Link className="hover:text-slate-900" href="/">
            Home
          </Link>
          <Link className="hover:text-slate-900" href="/marketplace">
            Marketplace
          </Link>
          <Link className="hover:text-slate-900" href="/pricing">
            Pricing
          </Link>
          <Link className="hover:text-slate-900" href="/about">
            About
          </Link>
          <Link className="hover:text-slate-900" href="/contact">
            Contact
          </Link>
        </nav>
        <div className="flex items-center gap-2">
          <Link className="btn-secondary px-3 py-2 text-sm" href="/login">
            Sign in
          </Link>
          <Link className="btn-primary px-3 py-2 text-sm" href="/signup">
            <Sparkles className="mr-1.5 h-4 w-4" />
            Get started
          </Link>
        </div>
      </div>
      <div className="border-t border-slate-100 px-6 py-2 text-sm md:hidden">
        <div className="mx-auto flex w-full max-w-6xl items-center gap-4 text-slate-700">
          <Link className="hover:text-slate-900" href="/">
            Home
          </Link>
          <Link className="hover:text-slate-900" href="/marketplace">
            Marketplace
          </Link>
          <Link className="hover:text-slate-900" href="/pricing">
            Pricing
          </Link>
        </div>
      </div>
    </header>
  );
}
