import { describe, expect, it } from 'vitest';
import { ExternalLinkAdapter } from './external-link-adapter';
import { StreamCapability } from './types';

describe('ExternalLinkAdapter', () => {
  const adapter = new ExternalLinkAdapter();

  it('validates external URLs', async () => {
    const valid = await adapter.validateSource({
      providerKey: 'external',
      externalUrl: 'https://example.com/live',
    });
    expect(valid.valid).toBe(true);
  });

  it('exposes external link capability', () => {
    expect(adapter.getCapabilities()).toContain(StreamCapability.EXTERNAL_LINK);
  });
});
