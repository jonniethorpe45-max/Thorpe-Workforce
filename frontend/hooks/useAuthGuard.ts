"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { getAuthToken } from "@/services/api";

export function useAuthGuard() {
  const router = useRouter();
  const [isAuthorized, setIsAuthorized] = useState(false);

  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    setIsAuthorized(true);
  }, [router]);

  return { isAuthorized };
}
