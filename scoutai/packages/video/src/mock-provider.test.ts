import { describe, expect, it } from 'vitest';
import { MockVideoStorageProvider } from './mock-provider';

describe('MockVideoStorageProvider', () => {
  it('supports upload lifecycle', async () => {
    const provider = new MockVideoStorageProvider();
    const session = await provider.createUpload({
      ownerUserId: 'user-1',
      contentType: 'video/mp4',
      fileName: 'clip.mp4',
      byteSize: 1024,
    });
    const asset = await provider.finalizeUpload({ assetId: session.assetId });
    expect(asset.status).toBe('ready');
    await provider.deleteAsset(asset.assetId);
  });
});
