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
    <div className="min-h-screen lg:flex">
      <Sidebar />
      <div className="flex-1">
        <Header />
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
