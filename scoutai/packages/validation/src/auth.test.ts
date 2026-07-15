import { describe, expect, it } from 'vitest';
import { loginRequestSchema, registerRequestSchema } from './auth';

describe('registerRequestSchema', () => {
  it('accepts a valid registration payload', () => {
    const result = registerRequestSchema.safeParse({
      email: 'athlete@example.com',
      password: 'securePass1',
    });
    expect(result.success).toBe(true);
  });

  it('rejects passwords without a number', () => {
    const result = registerRequestSchema.safeParse({
      email: 'athlete@example.com',
      password: 'onlyletters',
    });
    expect(result.success).toBe(false);
  });
});

describe('loginRequestSchema', () => {
  it('requires a password', () => {
    const result = loginRequestSchema.safeParse({
      email: 'athlete@example.com',
      password: '',
    });
    expect(result.success).toBe(false);
  });
});
