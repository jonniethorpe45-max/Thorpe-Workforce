function normalizeBaseUrl(value: string): string {
  return value.trim().replace(/\/+$/, "");
}

export function resolveServerApiBaseUrl(): string {
  const explicit = process.env.API_BASE_URL?.trim();
  if (explicit) return normalizeBaseUrl(explicit);

  const publicConfigured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (publicConfigured) return normalizeBaseUrl(publicConfigured);

  if (process.env.NODE_ENV !== "production") {
    return "http://localhost:8000";
  }

  throw new Error("Missing API base URL. Set API_BASE_URL or NEXT_PUBLIC_API_BASE_URL.");
}

export async function fetchServerApi(path: string, init?: RequestInit): Promise<Response> {
  const base = resolveServerApiBaseUrl();
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return fetch(`${base}${normalizedPath}`, {
    cache: "no-store",
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.headers ?? {})
    }
  });
}
