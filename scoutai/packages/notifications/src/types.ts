export type NotificationChannel = 'email' | 'sms' | 'push' | 'in_app';

export interface NotificationMessage {
  channel: NotificationChannel;
  to: string;
  subject?: string;
  body: string;
  metadata?: Record<string, string>;
}

export interface NotificationSendResult {
  id: string;
  status: 'queued' | 'sent' | 'failed';
}

export interface NotificationProvider {
  send(message: NotificationMessage): Promise<NotificationSendResult>;
}
