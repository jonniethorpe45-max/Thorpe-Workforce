import { Module } from '@nestjs/common';
import { AuthorizationModule } from '../authorization/authorization.module';
import { AdminController } from './admin.controller';

@Module({
  imports: [AuthorizationModule],
  controllers: [AdminController],
})
export class AdminModule {}
