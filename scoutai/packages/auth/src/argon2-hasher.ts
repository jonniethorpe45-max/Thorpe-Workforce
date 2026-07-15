import * as argon2 from 'argon2';
import type { PasswordHasher } from './types';

/**
 * Default password hasher using Argon2id.
 *
 * Authentication is provider-agnostic: swap this class for another `PasswordHasher`
 * implementation (bcrypt, external IdP token validation, etc.) at composition root.
 */
export class Argon2PasswordHasher implements PasswordHasher {
  async hash(plainText: string): Promise<string> {
    return argon2.hash(plainText, { type: argon2.argon2id });
  }

  async verify(plainText: string, passwordHash: string): Promise<boolean> {
    try {
      return await argon2.verify(passwordHash, plainText);
    } catch {
      return false;
    }
  }
}
