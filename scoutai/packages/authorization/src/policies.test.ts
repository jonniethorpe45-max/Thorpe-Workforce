import { describe, expect, it } from 'vitest';
import { UserRoleType } from '@scoutai/domain';
import { assertAuthenticated, canViewAdminSystemInfo, hasRole } from './policies';

describe('authorization policies', () => {
  const admin = { id: '1', roles: [UserRoleType.SCOUTAI_ADMIN] };
  const athlete = { id: '2', roles: [UserRoleType.ATHLETE] };

  it('detects roles', () => {
    expect(hasRole(admin, UserRoleType.SCOUTAI_ADMIN)).toBe(true);
    expect(hasRole(athlete, UserRoleType.SCOUTAI_ADMIN)).toBe(false);
  });

  it('requires authentication', () => {
    expect(assertAuthenticated(null).allowed).toBe(false);
    expect(assertAuthenticated(athlete).allowed).toBe(true);
  });

  it('restricts admin system info', () => {
    expect(canViewAdminSystemInfo(admin).allowed).toBe(true);
    expect(canViewAdminSystemInfo(athlete).allowed).toBe(false);
  });
});
