import type { Logger } from '@scoutai/observability';
import type { UserRoleType } from '@scoutai/domain';
import type { UserStatus } from '@scoutai/database';

export interface AuthenticatedUser {
  id: string;
  email: string;
  roles: UserRoleType[];
  status: UserStatus;
}

declare global {
  namespace Express {
    interface Request {
      requestId: string;
      logger: Logger;
      user?: AuthenticatedUser;
    }
  }
}

export {};
