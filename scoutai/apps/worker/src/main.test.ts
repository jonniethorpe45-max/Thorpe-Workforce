import { describe, expect, it } from 'vitest';
import { SMOKE_JOB_NAME, SYSTEM_QUEUE } from './main';

describe('worker constants', () => {
  it('uses the scoutai-system queue and system.smoke job name', () => {
    expect(SYSTEM_QUEUE).toBe('scoutai-system');
    expect(SMOKE_JOB_NAME).toBe('system.smoke');
  });
});
