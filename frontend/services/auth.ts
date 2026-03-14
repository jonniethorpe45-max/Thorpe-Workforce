import { api, clearAuthToken, setAuthToken } from "@/services/api";

type LoginPayload = {
  email: string;
  password: string;
};

type SignupPayload = {
  full_name: string;
  email: string;
  password: string;
  company_name: string;
  website?: string;
  industry?: string;
};

export async function login(payload: LoginPayload) {
  const data = await api.post<{ access_token: string }>("/auth/login", payload);
  setAuthToken(data.access_token);
  return data;
}

export async function signup(payload: SignupPayload) {
  const data = await api.post<{ access_token: string }>("/auth/signup", payload);
  setAuthToken(data.access_token);
  return data;
}

export async function logout() {
  try {
    await api.post("/auth/logout", {});
  } finally {
    clearAuthToken();
  }
}
