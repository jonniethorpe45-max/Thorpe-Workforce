const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:4000';

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly body?: unknown,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function parseJsonSafe(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) {
    return undefined;
  }
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  return fetch(`${API_URL}${path}`, {
    ...init,
    credentials: 'include',
    headers,
  });
}

export async function apiJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await apiFetch(path, init);
  const body = await parseJsonSafe(response);

  if (!response.ok) {
    const message =
      typeof body === 'object' && body !== null && 'message' in body
        ? String((body as { message: unknown }).message)
        : `Request failed with status ${response.status}`;
    throw new ApiError(message, response.status, body);
  }

  return body as T;
}

export interface AuthUser {
  id: string;
  email: string;
  roles: string[];
}

export interface HealthResponse {
  status: string;
}

export interface ReadyDependency {
  name: string;
  status: 'ok' | 'error';
  message?: string;
}

export interface ReadyResponse {
  status: string;
  dependencies?: ReadyDependency[];
}

export function login(email: string, password: string): Promise<AuthUser> {
  return apiJson<AuthUser>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export function register(email: string, password: string): Promise<AuthUser> {
  return apiJson<AuthUser>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export function getMe(): Promise<AuthUser> {
  return apiJson<AuthUser>('/me');
}

export function getHealth(): Promise<HealthResponse> {
  return apiJson<HealthResponse>('/health');
}

export function getReady(): Promise<ReadyResponse> {
  return apiJson<ReadyResponse>('/ready');
}

export function getApiUrl(): string {
  return API_URL;
}
