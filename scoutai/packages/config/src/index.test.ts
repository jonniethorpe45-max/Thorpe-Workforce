import { describe, expect, it } from 'vitest';
import { loadEnv, resetEnvCache } from './index';

describe('loadEnv', () => {
  it('fails clearly when SESSION_SECRET is too short', () => {
    resetEnvCache();
    expect(() =>
      loadEnv({
        DATABASE_URL: 'postgresql://scoutai:scoutai@127.0.0.1:5432/scoutai',
        REDIS_URL: 'redis://127.0.0.1:6379',
        SESSION_SECRET: 'too-short',
      }),
    ).toThrow(/SESSION_SECRET/);
  });

  it('loads valid environment', () => {
    resetEnvCache();
    const env = loadEnv({
      DATABASE_URL: 'postgresql://scoutai:scoutai@127.0.0.1:5432/scoutai',
      REDIS_URL: 'redis://127.0.0.1:6379',
      SESSION_SECRET: 'dev-only-change-me-to-a-long-random-string',
    });
    expect(env.API_PORT).toBe(4000);
    expect(env.COOKIE_SECURE).toBe(false);
  });
});
