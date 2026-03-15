import Link from "next/link";

const INTERNAL_BUILDER_ENABLED = process.env.NEXT_PUBLIC_INTERNAL_WORKER_BUILDER_ENABLED === "true";

export default function SettingsPage() {
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Settings</h2>
      <div className="card p-6">
        <p className="text-sm text-slate-600">
          Workspace controls for team access and operational settings are managed here.
        </p>
        <Link href="/app/settings/billing" className="mt-3 inline-block text-sm font-medium text-brand-700 hover:underline">
          Open Billing & Plan Settings
        </Link>
        <div className="mt-3 space-y-1 text-sm">
          <p>
            <Link href="/app/onboarding" className="font-medium text-brand-700 hover:underline">
              Resume onboarding
            </Link>
          </p>
          <p>
            <Link href="/contact" className="font-medium text-brand-700 hover:underline">
              Contact support
            </Link>
          </p>
        </div>
      </div>
      {INTERNAL_BUILDER_ENABLED ? (
        <div className="card border-amber-200 bg-amber-50 p-6">
          <h3 className="text-base font-semibold text-amber-900">Internal Tools</h3>
          <p className="mt-1 text-sm text-amber-800">
            Worker Builder is intended for internal architecture testing and is hidden unless enabled via environment flag.
          </p>
          <Link href="/app/internal/worker-builder" className="mt-3 inline-block text-sm font-medium text-brand-700 hover:underline">
            Open Internal Worker Builder
          </Link>
        </div>
      ) : null}
    </div>
  );
}
