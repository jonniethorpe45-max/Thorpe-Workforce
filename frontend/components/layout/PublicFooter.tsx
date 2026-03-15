import Link from "next/link";

export function PublicFooter() {
  return (
    <footer className="border-t border-slate-200/60 bg-slate-950/85">
      <div className="mx-auto grid w-full max-w-6xl gap-6 px-6 py-10 md:grid-cols-3">
        <div>
          <p className="text-sm font-semibold text-slate-100">Thorpe Workforce</p>
          <p className="mt-2 text-sm text-slate-600">
            Deploy AI workers, automate operations, and monetize high-value worker templates.
          </p>
        </div>
        <div className="space-y-1 text-sm text-slate-600">
          <p className="font-medium text-slate-800">Product</p>
          <p><Link href="/marketplace" className="hover:text-slate-900">Marketplace</Link></p>
          <p><Link href="/pricing" className="hover:text-slate-900">Pricing</Link></p>
          <p><Link href="/workers" className="hover:text-slate-900">Public Workers</Link></p>
        </div>
        <div className="space-y-1 text-sm text-slate-600">
          <p className="font-medium text-slate-800">Trust & Legal</p>
          <p><Link href="/privacy" className="hover:text-slate-900">Privacy</Link></p>
          <p><Link href="/terms" className="hover:text-slate-900">Terms</Link></p>
          <p><Link href="/acceptable-use" className="hover:text-slate-900">Acceptable Use</Link></p>
          <p><Link href="/contact" className="hover:text-slate-900">Support</Link></p>
        </div>
      </div>
    </footer>
  );
}
