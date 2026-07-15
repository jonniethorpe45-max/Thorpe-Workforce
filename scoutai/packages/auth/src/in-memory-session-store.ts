import { randomUUID } from 'node:crypto';
import type { SessionRecord, SessionStore } from './types';

export class InMemorySessionStore implements SessionStore {
  private readonly sessions = new Map<string, SessionRecord>();

  async create(userId: string, ttlSeconds: number): Promise<SessionRecord> {
    const now = new Date();
    const record: SessionRecord = {
      id: randomUUID(),
      userId,
      createdAt: now,
      expiresAt: new Date(now.getTime() + ttlSeconds * 1000),
    };
    this.sessions.set(record.id, record);
    return record;
  }

  async get(sessionId: string): Promise<SessionRecord | null> {
    const record = this.sessions.get(sessionId);
    if (!record) {
      return null;
    }
    if (record.expiresAt.getTime() <= Date.now()) {
      this.sessions.delete(sessionId);
      return null;
    }
    return record;
  }

  async delete(sessionId: string): Promise<void> {
    this.sessions.delete(sessionId);
  }

  async deleteAllForUser(userId: string): Promise<void> {
    for (const [sessionId, record] of this.sessions.entries()) {
      if (record.userId === userId) {
        this.sessions.delete(sessionId);
      }
    }
  }
}
