"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { Bell, Command, LifeBuoy, LogOut, Settings2 } from "lucide-react";

import { logout } from "@/services/auth";

export function Header() {
  const router = useRouter();
  return (
    <header className="sticky top-0 z-20 flex items-center justify-between border-b border-slate-200/60 bg-slate-950/75 px-6 py-4 backdrop-blur-xl">
      <div>
        <p className="inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">
          <Command className="h-3 w-3" />
          Thorpe Workforce
        </p>
        <h1 className="bg-gradient-to-r from-slate-100 via-cyan-100 to-indigo-300 bg-clip-text text-lg font-semibold text-transparent">
          AI Command Center
        </h1>
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="btn-secondary hidden h-10 w-10 rounded-full p-0 md:inline-flex"
          aria-label="Notifications"
          title="Notifications"
        >
          <Bell className="h-4 w-4" />
        </button>
        <Link className="btn-secondary" href="/app/settings">
          <Settings2 className="mr-1.5 h-4 w-4" />
          Settings
        </Link>
        <Link className="btn-secondary" href="/contact">
          <LifeBuoy className="mr-1.5 h-4 w-4" />
          Support
        </Link>
        <button
          className="btn-secondary"
          onClick={async () => {
            await logout();
            router.push("/login");
          }}
        >
          <LogOut className="mr-1.5 h-4 w-4" />
          Log out
        </button>
      </div>
    </header>
  );
}
