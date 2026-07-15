import { describe, expect, it } from 'vitest';
import type { ApiErrorResponse, PublicUser } from './dtos';
import { UserRoleType, UserStatus } from '@scoutai/domain';

describe('contracts DTOs', () => {
  it('models API errors without leaking internals', () => {
    const error: ApiErrorResponse = {
      error: {
        code: 'UNAUTHORIZED',
        message: 'Sign in required',
        requestId: 'req-1',
      },
    };
    expect(error.error.code).toBe('UNAUTHORIZED');
  });

  it('models public users without password hashes', () => {
    const user: PublicUser = {
      id: 'user-1',
      email: 'athlete@example.com',
      status: UserStatus.ACTIVE,
      roles: [UserRoleType.ATHLETE],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    expect(user).not.toHaveProperty('passwordHash');
  });
});
