import { randomUUID } from 'node:crypto';
import type {
  NotificationMessage,
  NotificationProvider,
  NotificationSendResult,
} from './types';

const sentMessages: NotificationMessage[] = [];

export function getSent(): readonly NotificationMessage[] {
  return sentMessages;
}

export function clearSent(): void {
  sentMessages.length = 0;
}

export class MockNotificationProvider implements NotificationProvider {
  async send(message: NotificationMessage): Promise<NotificationSendResult> {
    sentMessages.push({ ...message });
    return {
      id: randomUUID(),
      status: 'sent',
    };
  }
}
