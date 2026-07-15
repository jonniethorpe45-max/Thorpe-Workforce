import { randomUUID } from 'node:crypto';
import { UserRoleType, UserStatus } from '@scoutai/domain';

export interface FakeUserOptions {
  id?: string;
  email?: string;
  status?: (typeof UserStatus)[keyof typeof UserStatus];
  roles?: Array<(typeof UserRoleType)[keyof typeof UserRoleType]>;
}

export interface FakeUser {
  id: string;
  email: string;
  status: (typeof UserStatus)[keyof typeof UserStatus];
  roles: Array<(typeof UserRoleType)[keyof typeof UserRoleType]>;
}

export function createFakeUser(options: FakeUserOptions = {}): FakeUser {
  return {
    id: options.id ?? randomUUID(),
    email: options.email ?? `user-${randomUUID().slice(0, 8)}@example.com`,
    status: options.status ?? UserStatus.ACTIVE,
    roles: options.roles ?? [UserRoleType.ATHLETE],
  };
}

export function wait(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

export async function expectError(
  fn: () => unknown | Promise<unknown>,
  matcher?: RegExp | string,
): Promise<Error> {
  try {
    await fn();
  } catch (error) {
    if (!(error instanceof Error)) {
      throw new Error(`Expected Error but received: ${String(error)}`);
    }
    if (matcher) {
      const message = typeof matcher === 'string' ? matcher : matcher.source;
      const passes =
        typeof matcher === 'string'
          ? error.message.includes(matcher)
          : matcher.test(error.message);
      if (!passes) {
        throw new Error(`Expected error matching ${message} but got: ${error.message}`);
      }
    }
    return error;
  }
  throw new Error('Expected function to throw');
}
