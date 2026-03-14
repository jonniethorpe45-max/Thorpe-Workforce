const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("thorpe_token");
}

export function setAuthToken(token: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem("thorpe_token", token);
  document.cookie = `thorpe_token=${token}; path=/; max-age=604800; samesite=lax`;
}

export function clearAuthToken() {
  if (typeof window === "undefined") return;
  localStorage.removeItem("thorpe_token");
  document.cookie = "thorpe_token=; path=/; max-age=0; samesite=lax";
}

type RequestOptions = {
  headers?: Record<string, string>;
};

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers || {})
    }
  });
  if (!res.ok) {
    const message = await res.text();
    throw new Error(message || `Request failed (${res.status})`);
  }
  return res.json();
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, {
      method: "GET",
      headers: options?.headers
    }),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
      headers: options?.headers
    }),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, {
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
      headers: options?.headers
    })
};
