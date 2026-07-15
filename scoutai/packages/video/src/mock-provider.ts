import { randomUUID } from 'node:crypto';
import type {
  CreateUploadRequest,
  FinalizeUploadRequest,
  UploadSession,
  VideoAsset,
  VideoStorageProvider,
} from './types';

export class MockVideoStorageProvider implements VideoStorageProvider {
  private readonly assets = new Map<string, VideoAsset>();

  async createUpload(request: CreateUploadRequest): Promise<UploadSession> {
    const assetId = randomUUID();
    const expiresAt = new Date(Date.now() + 60 * 60 * 1000).toISOString();
    this.assets.set(assetId, {
      assetId,
      ownerUserId: request.ownerUserId,
      playbackUrl: `https://video.mock/${assetId}`,
      status: 'processing',
      createdAt: new Date().toISOString(),
    });
    return {
      assetId,
      uploadUrl: `https://upload.mock/${assetId}`,
      expiresAt,
    };
  }

  async finalizeUpload(request: FinalizeUploadRequest): Promise<VideoAsset> {
    const existing = this.assets.get(request.assetId);
    if (!existing) {
      throw new Error(`Asset not found: ${request.assetId}`);
    }
    const ready: VideoAsset = { ...existing, status: 'ready' };
    this.assets.set(request.assetId, ready);
    return ready;
  }

  async deleteAsset(assetId: string): Promise<void> {
    this.assets.delete(assetId);
  }
}
