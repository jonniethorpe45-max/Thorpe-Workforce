import { normalizeEmail } from '../auth/auth.utils';

export function toPublicUser(user: {
  id: string;
  email: string;
  status: string;
  roles: Array<{ role: string }>;
}) {
  return {
    id: user.id,
    email: user.email,
    status: user.status,
    roles: user.roles.map((entry) => entry.role),
  };
}

export { normalizeEmail };
