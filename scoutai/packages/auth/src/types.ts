import type { UserRoleType } from '@scoutai/domain';

export interface AuthUser {
  id: string;
  email: string;
  roles: UserRoleType[];
}

export interface SessionRecord {
  id: string;
  userId: string;
  createdAt: Date;
  expiresAt: Date;
}

export interface PasswordHasher {
  hash(plainText: string): Promise<string>;
  verify(plainText: string, passwordHash: string): Promise<boolean>;
}

export interface SessionStore {
  create(userId: string, ttlSeconds: number): Promise<SessionRecord>;
  get(sessionId: string): Promise<SessionRecord | null>;
  delete(sessionId: string): Promise<void>;
  deleteAllForUser(userId: string): Promise<void>;
}

export interface CookieSessionOptions {
  httpOnly: boolean;
  sameSite: 'lax' | 'strict' | 'none';
  secure: boolean;
  maxAge: number;
}
