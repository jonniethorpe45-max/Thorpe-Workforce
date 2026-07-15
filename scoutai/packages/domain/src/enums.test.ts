import { describe, expect, it } from 'vitest';
import { UserRoleType, UserStatus } from './enums';

describe('domain enums', () => {
  it('exposes stable user status values', () => {
    expect(UserStatus.ACTIVE).toBe('ACTIVE');
    expect(UserStatus.DISABLED).toBe('DISABLED');
    expect(UserStatus.PENDING).toBe('PENDING');
  });

  it('exposes scoutai admin role', () => {
    expect(UserRoleType.SCOUTAI_ADMIN).toBe('SCOUTAI_ADMIN');
  });
});
