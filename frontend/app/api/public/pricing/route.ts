import { NextResponse } from "next/server";

import { fetchServerApi } from "@/lib/serverApi";

export async function GET() {
  try {
    const upstream = await fetchServerApi("/billing/plans");
    const body = await upstream.json().catch(() => null);
    if (!upstream.ok) {
      return NextResponse.json(
        { detail: (body as { detail?: string } | null)?.detail || "Failed to load pricing plans." },
        { status: upstream.status }
      );
    }
    return NextResponse.json(body, { status: 200 });
  } catch {
    return NextResponse.json({ detail: "Unable to reach pricing service right now." }, { status: 503 });
  }
}
