import {
  StreamCapability,
  type PlaybackAccess,
  type StreamProviderAdapter,
  type StreamSource,
  type StreamStatus,
  type StreamValidationResult,
} from './types';

const URL_PATTERN = /^https?:\/\/.+/i;

export class ExternalLinkAdapter implements StreamProviderAdapter {
  async validateSource(source: StreamSource): Promise<StreamValidationResult> {
    if (!source.externalUrl || !URL_PATTERN.test(source.externalUrl)) {
      return { valid: false, reason: 'A valid external URL is required' };
    }
    return { valid: true };
  }

  async getPlaybackAccess(source: StreamSource): Promise<PlaybackAccess> {
    const validation = await this.validateSource(source);
    if (!validation.valid || !source.externalUrl) {
      throw new Error(validation.reason ?? 'Invalid external stream source');
    }
    return {
      playbackUrl: source.externalUrl,
      expiresAt: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
      capabilities: this.getCapabilities(),
    };
  }

  async getStatus(source: StreamSource): Promise<StreamStatus> {
    const validation = await this.validateSource(source);
    if (!validation.valid) {
      return { state: 'error' };
    }
    return { state: 'live', viewerCount: 0 };
  }

  getCapabilities(): StreamCapability[] {
    return [StreamCapability.EXTERNAL_LINK, StreamCapability.LIVE_PLAYBACK];
  }
}
