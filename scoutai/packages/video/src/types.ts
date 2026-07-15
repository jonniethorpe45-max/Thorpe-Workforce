export interface CreateUploadRequest {
  ownerUserId: string;
  contentType: string;
  fileName: string;
  byteSize: number;
}

export interface UploadSession {
  assetId: string;
  uploadUrl: string;
  expiresAt: string;
}

export interface FinalizeUploadRequest {
  assetId: string;
}

export interface VideoAsset {
  assetId: string;
  ownerUserId: string;
  playbackUrl: string;
  status: 'processing' | 'ready' | 'failed';
  createdAt: string;
}

export interface VideoStorageProvider {
  createUpload(request: CreateUploadRequest): Promise<UploadSession>;
  finalizeUpload(request: FinalizeUploadRequest): Promise<VideoAsset>;
  deleteAsset(assetId: string): Promise<void>;
}
