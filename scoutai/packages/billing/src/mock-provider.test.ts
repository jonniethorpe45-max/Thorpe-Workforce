import { describe, expect, it } from 'vitest';
import { MockBillingProvider } from './mock-provider';

describe('MockBillingProvider', () => {
  it('returns empty entitlements', async () => {
    const provider = new MockBillingProvider();
    const entitlements = await provider.getEntitlements({ userId: 'user-1' });
    expect(entitlements).toEqual([]);
  });
});
