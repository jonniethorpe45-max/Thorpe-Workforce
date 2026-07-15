import { Controller, Get, HttpStatus, Inject, Res } from '@nestjs/common';
import { checkDatabaseConnectivity } from '@scoutai/database';
import type { Response } from 'express';
import { PrismaService } from '../database/prisma.service';
import { RedisService } from '../redis/redis.service';

@Controller('health')
export class HealthController {
  constructor(
    @Inject(PrismaService) private readonly prisma: PrismaService,
    @Inject(RedisService) private readonly redis: RedisService,
  ) {}

  @Get()
  getHealth() {
    return {
      status: 'ok',
      service: 'scoutai-api',
    };
  }

  @Get('ready')
  async getReadiness(@Res() response: Response) {
    let postgres = false;
    let redis = false;

    try {
      await checkDatabaseConnectivity(this.prisma.client);
      postgres = true;
    } catch {
      postgres = false;
    }

    try {
      redis = await this.redis.ping();
    } catch {
      redis = false;
    }

    const ready = postgres && redis;
    const status = ready ? 'ok' : 'degraded';

    response.status(ready ? HttpStatus.OK : HttpStatus.SERVICE_UNAVAILABLE).json({
      status,
      checks: {
        postgres,
        redis,
      },
    });
  }
}
