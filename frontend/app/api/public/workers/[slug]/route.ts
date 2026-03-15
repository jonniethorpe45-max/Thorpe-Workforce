import { NextResponse } from "next/server";

import { fetchServerApi } from "@/lib/serverApi";

export async function GET(_: Request, context: { params: Promise<{ slug: string }> }) {
  const params = await context.params;
  const slug = (params.slug || "").trim();
  if (!slug) {
    return NextResponse.json({ detail: "Worker slug is required." }, { status: 400 });
  }
  try {
    const upstream = await fetchServerApi(`/public-workers/${encodeURIComponent(slug)}`);
    const body = await upstream.json().catch(() => null);
    if (!upstream.ok) {
      return NextResponse.json(
        { detail: (body as { detail?: string } | null)?.detail || "Failed to load worker details." },
        { status: upstream.status }
      );
    }
    return NextResponse.json(body, { status: 200 });
  } catch {
    return NextResponse.json({ detail: "Unable to reach worker details right now." }, { status: 503 });
  }
}
