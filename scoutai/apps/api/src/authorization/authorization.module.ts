import { Module } from '@nestjs/common';
import { AuthModule } from '../auth/auth.module';
import { AdminGuard } from './admin.guard';

@Module({
  imports: [AuthModule],
  providers: [AdminGuard],
  exports: [AdminGuard, AuthModule],
})
export class AuthorizationModule {}
