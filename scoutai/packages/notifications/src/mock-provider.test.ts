import { describe, expect, it, beforeEach } from 'vitest';
import { MockNotificationProvider, clearSent, getSent } from './mock-provider';

describe('MockNotificationProvider', () => {
  beforeEach(() => {
    clearSent();
  });

  it('records sent messages', async () => {
    const provider = new MockNotificationProvider();
    await provider.send({
      channel: 'email',
      to: 'user@example.com',
      subject: 'Welcome',
      body: 'Hello',
    });
    expect(getSent()).toHaveLength(1);
    expect(getSent()[0]?.to).toBe('user@example.com');
  });
});
