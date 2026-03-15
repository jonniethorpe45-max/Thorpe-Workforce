"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";

import { logout } from "@/services/auth";

export function Header() {
  const router = useRouter();
  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
      <div>
        <p className="text-xs font-semibold uppercase text-slate-500">Thorpe Workforce</p>
        <h1 className="text-lg font-semibold text-slate-900">AI Employee Mission Control</h1>
      </div>
      <div className="flex items-center gap-2">
        <Link className="btn-secondary" href="/app/settings">
          Settings
        </Link>
        <Link className="btn-secondary" href="/contact">
          Support
        </Link>
        <button
          className="btn-secondary"
          onClick={async () => {
            await logout();
            router.push("/login");
          }}
        >
          Log out
        </button>
      </div>
    </header>
  );
}
