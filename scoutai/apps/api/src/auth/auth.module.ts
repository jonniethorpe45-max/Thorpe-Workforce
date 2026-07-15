import { Module } from '@nestjs/common';
import { RateLimitGuard } from '../common/rate-limit.guard';
import { AuthController } from './auth.controller';
import { AuthGuard } from './auth.guard';
import { AuthService } from './auth.service';
import { SessionService } from './session.service';

@Module({
  controllers: [AuthController],
  providers: [AuthService, SessionService, AuthGuard, RateLimitGuard],
  exports: [AuthService, SessionService, AuthGuard],
})
export class AuthModule {}
