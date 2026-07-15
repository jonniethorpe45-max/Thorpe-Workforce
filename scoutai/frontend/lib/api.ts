export type Source = {
  title: string;
  url?: string | null;
  note?: string | null;
};

export type Finding = {
  title: string;
  detail: string;
  confidence: "low" | "medium" | "high";
  source_indexes: number[];
};

export type ResearchBrief = {
  query: string;
  focus: string;
  depth: string;
  summary: string;
  findings: Finding[];
  risks: string[];
  next_actions: string[];
  sources: Source[];
  mode: "demo" | "live";
};

export type ResearchRequest = {
  query: string;
  focus?: "general" | "market" | "competitor" | "product";
  depth?: "quick" | "standard" | "deep";
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function runResearch(body: ResearchRequest): Promise<ResearchBrief> {
  const res = await fetch(`${API_URL}/research`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: body.query,
      focus: body.focus ?? "general",
      depth: body.depth ?? "standard",
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Research failed (${res.status})`);
  }

  return res.json();
}
