import { UserRoleType, type UserRoleType as UserRole } from '@scoutai/domain';

export interface AuthorizationSubject {
  id: string;
  roles: UserRole[];
}

export interface AuthorizationResult {
  allowed: boolean;
  reason?: string;
}

export function hasRole(subject: AuthorizationSubject | null | undefined, role: UserRole): boolean {
  if (!subject) {
    return false;
  }
  return subject.roles.includes(role);
}

export function isScoutAiAdmin(subject: AuthorizationSubject | null | undefined): boolean {
  return hasRole(subject, UserRoleType.SCOUTAI_ADMIN);
}

export function assertAuthenticated(
  subject: AuthorizationSubject | null | undefined,
): AuthorizationResult {
  if (!subject) {
    return { allowed: false, reason: 'Authentication required' };
  }
  return { allowed: true };
}

export function canViewAdminSystemInfo(
  subject: AuthorizationSubject | null | undefined,
): AuthorizationResult {
  const auth = assertAuthenticated(subject);
  if (!auth.allowed) {
    return auth;
  }
  if (!isScoutAiAdmin(subject)) {
    return { allowed: false, reason: 'ScoutAI admin role required' };
  }
  return { allowed: true };
}
