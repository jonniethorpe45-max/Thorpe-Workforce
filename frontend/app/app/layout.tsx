"use client";

import type { ReactNode } from "react";

import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { LoadingState } from "@/components/ui/LoadingState";
import { useAuthGuard } from "@/hooks/useAuthGuard";

export default function AppLayout({ children }: { children: ReactNode }) {
  const { isAuthorized } = useAuthGuard();
  if (!isAuthorized) {
    return (
      <main className="mx-auto mt-10 max-w-3xl px-6">
        <LoadingState label="Checking your session..." />
      </main>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950/60 lg:flex">
      <Sidebar />
      <div className="flex-1 bg-gradient-to-b from-slate-950/40 via-slate-900/30 to-slate-950/50">
        <Header />
        <main className="p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
