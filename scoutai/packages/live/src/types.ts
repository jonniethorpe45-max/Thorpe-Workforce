export const StreamCapability = {
  LIVE_PLAYBACK: 'LIVE_PLAYBACK',
  DVR: 'DVR',
  CHAT: 'CHAT',
  MULTI_ANGLE: 'MULTI_ANGLE',
  EXTERNAL_LINK: 'EXTERNAL_LINK',
} as const;
export type StreamCapability = (typeof StreamCapability)[keyof typeof StreamCapability];

export interface StreamSource {
  providerKey: string;
  externalUrl?: string;
  streamKey?: string;
}

export interface StreamValidationResult {
  valid: boolean;
  reason?: string;
}

export interface PlaybackAccess {
  playbackUrl: string;
  expiresAt: string;
  capabilities: StreamCapability[];
}

export interface StreamStatus {
  state: 'idle' | 'starting' | 'live' | 'ended' | 'error';
  viewerCount?: number;
  startedAt?: string;
  endedAt?: string;
}

export interface StreamProviderAdapter {
  validateSource(source: StreamSource): Promise<StreamValidationResult>;
  getPlaybackAccess(source: StreamSource): Promise<PlaybackAccess>;
  getStatus(source: StreamSource): Promise<StreamStatus>;
  getCapabilities(): StreamCapability[];
}
