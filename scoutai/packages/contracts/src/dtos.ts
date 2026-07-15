import type { UserRoleType, UserStatus } from '@scoutai/domain';

export interface ApiErrorBody {
  code: string;
  message: string;
  requestId: string;
}

export interface ApiErrorResponse {
  error: ApiErrorBody;
}

export interface PublicUser {
  id: string;
  email: string;
  status: UserStatus;
  roles: UserRoleType[];
  createdAt: string;
  updatedAt: string;
}

export interface AuthSessionUser {
  id: string;
  email: string;
  roles: UserRoleType[];
}

export interface HealthResponse {
  status: 'ok';
  timestamp: string;
}

export interface ReadyResponse {
  status: 'ready' | 'not_ready';
  checks: {
    database: boolean;
    redis: boolean;
  };
  timestamp: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface MeResponse {
  user: AuthSessionUser;
}

export interface SystemInfoResponse {
  version: string;
  environment: string;
  buildSha?: string;
  startedAt: string;
}
