import { describe, expect, it } from 'vitest';
import { UserRoleType } from '@scoutai/domain';
import { createFakeUser, expectError } from './helpers';

describe('testing helpers', () => {
  it('creates fake users with defaults', () => {
    const user = createFakeUser();
    expect(user.roles).toContain(UserRoleType.ATHLETE);
    expect(user.email).toContain('@example.com');
  });

  it('expects errors', async () => {
    const error = await expectError(() => {
      throw new Error('boom');
    }, /boom/);
    expect(error.message).toBe('boom');
  });
});
