"use client";

import { useRouter } from "next/navigation";

import { logout } from "@/services/auth";

export function Header() {
  const router = useRouter();
  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
      <div>
        <p className="text-xs font-semibold uppercase text-slate-500">Thorpe Workforce</p>
        <h1 className="text-lg font-semibold text-slate-900">AI Sales Worker Control Center</h1>
      </div>
      <button
        className="btn-secondary"
        onClick={async () => {
          await logout();
          router.push("/login");
        }}
      >
        Log out
      </button>
    </header>
  );
}
