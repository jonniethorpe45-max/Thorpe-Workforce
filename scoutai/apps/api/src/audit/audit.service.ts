import { Global, Inject, Injectable } from '@nestjs/common';
import type { Prisma } from '@scoutai/database';
import { PrismaService } from '../database/prisma.service';

export interface AuditEventInput {
  actorType: string;
  actorId?: string | null;
  action: string;
  targetType: string;
  targetId?: string | null;
  requestId?: string | null;
  metadata?: Prisma.InputJsonValue;
}

@Global()
@Injectable()
export class AuditService {
  constructor(@Inject(PrismaService) private readonly prisma: PrismaService) {}

  async record(event: AuditEventInput): Promise<void> {
    await this.prisma.client.auditEvent.create({
      data: {
        actorType: event.actorType,
        actorId: event.actorId ?? null,
        action: event.action,
        targetType: event.targetType,
        targetId: event.targetId ?? null,
        requestId: event.requestId ?? null,
        metadata: event.metadata ?? undefined,
      },
    });
  }
}
