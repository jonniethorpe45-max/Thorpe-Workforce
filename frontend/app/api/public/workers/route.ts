import { NextRequest, NextResponse } from "next/server";

import { fetchServerApi } from "@/lib/serverApi";

export async function GET(request: NextRequest) {
  const query = request.nextUrl.search || "";
  try {
    const upstream = await fetchServerApi(`/public-workers${query}`);
    const body = await upstream.json().catch(() => null);
    if (!upstream.ok) {
      return NextResponse.json(
        { detail: (body as { detail?: string } | null)?.detail || "Failed to load marketplace workers." },
        { status: upstream.status }
      );
    }
    return NextResponse.json(body, { status: 200 });
  } catch {
    return NextResponse.json({ detail: "Unable to reach worker library right now." }, { status: 503 });
  }
}
