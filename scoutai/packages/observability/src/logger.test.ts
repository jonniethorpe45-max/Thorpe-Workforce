import { describe, expect, it } from 'vitest';
import { createRequestId, sanitizeRecord, serializeError } from './logger';

describe('observability', () => {
  it('redacts sensitive fields', () => {
    const sanitized = sanitizeRecord({
      email: 'user@example.com',
      password: 'secret123',
      apiKey: 'abc',
    });
    expect(sanitized.email).toBe('user@example.com');
    expect(sanitized.password).toBe('[REDACTED]');
    expect(sanitized.apiKey).toBe('[REDACTED]');
  });

  it('serializes errors', () => {
    const serialized = serializeError(new Error('boom'));
    expect(serialized.name).toBe('Error');
    expect(serialized.message).toBe('boom');
  });

  it('creates request ids', () => {
    expect(createRequestId()).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
    );
  });
});
