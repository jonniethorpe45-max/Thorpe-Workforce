import Link from "next/link";

export function PublicNav() {
  return (
    <header className="border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-lg font-semibold text-slate-900">
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
