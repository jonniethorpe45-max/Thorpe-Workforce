import { describe, expect, it } from 'vitest';
import { Argon2PasswordHasher } from './argon2-hasher';
import { InMemorySessionStore } from './in-memory-session-store';

describe('Argon2PasswordHasher', () => {
  it('hashes and verifies passwords', async () => {
    const hasher = new Argon2PasswordHasher();
    const hash = await hasher.hash('securePass1');
    expect(hash).not.toBe('securePass1');
    expect(await hasher.verify('securePass1', hash)).toBe(true);
    expect(await hasher.verify('wrong', hash)).toBe(false);
  });
});

describe('InMemorySessionStore', () => {
  it('creates and retrieves sessions', async () => {
    const store = new InMemorySessionStore();
    const session = await store.create('user-1', 3600);
    const loaded = await store.get(session.id);
    expect(loaded?.userId).toBe('user-1');
  });
});
