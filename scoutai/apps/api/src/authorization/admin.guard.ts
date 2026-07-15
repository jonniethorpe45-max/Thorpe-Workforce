import {
  CanActivate,
  ExecutionContext,
  ForbiddenException,
  Inject,
  Injectable,
} from '@nestjs/common';
import { canViewAdminSystemInfo } from '@scoutai/authorization';
import type { Request } from 'express';
import { AuthGuard } from '../auth/auth.guard';

@Injectable()
export class AdminGuard implements CanActivate {
  constructor(@Inject(AuthGuard) private readonly authGuard: AuthGuard) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const authenticated = await this.authGuard.canActivate(context);
    if (!authenticated) {
      return false;
    }

    const request = context.switchToHttp().getRequest<Request>();
    const result = canViewAdminSystemInfo(request.user ?? null);
    if (!result.allowed) {
      throw new ForbiddenException({
        code: 'FORBIDDEN',
        message: result.reason ?? 'Forbidden',
      });
    }

    return true;
  }
}
