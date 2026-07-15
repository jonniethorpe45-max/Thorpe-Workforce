import { Controller, Get, Inject, Req, UseGuards } from '@nestjs/common';
import { getEnv } from '@scoutai/config';
import type { Request } from 'express';
import { AuditService } from '../audit/audit.service';
import { AdminGuard } from '../authorization/admin.guard';

@Controller('admin')
export class AdminController {
  constructor(@Inject(AuditService) private readonly auditService: AuditService) {}

  @Get('system-info')
  @UseGuards(AdminGuard)
  async getSystemInfo(@Req() request: Request) {
    const env = getEnv();

    await this.auditService.record({
      actorType: 'user',
      actorId: request.user?.id ?? null,
      action: 'admin.system_info.access',
      targetType: 'system',
      targetId: null,
      requestId: request.requestId,
    });

    return {
      environment: env.NODE_ENV,
      service: 'scoutai-api',
      nodeVersion: process.version,
      timestamp: new Date().toISOString(),
    };
  }
}
