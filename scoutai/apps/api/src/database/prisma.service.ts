import { Global, Injectable, OnModuleDestroy } from '@nestjs/common';
import { getPrismaClient, type PrismaClient } from '@scoutai/database';

@Global()
@Injectable()
export class PrismaService implements OnModuleDestroy {
  readonly client: PrismaClient = getPrismaClient();

  async onModuleDestroy(): Promise<void> {
    await this.client.$disconnect();
  }
}
