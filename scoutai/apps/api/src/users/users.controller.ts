import { Controller, Get, Req, UseGuards } from '@nestjs/common';
import type { UserRoleType } from '@scoutai/domain';
import type { Request } from 'express';
import { AuthGuard } from '../auth/auth.guard';

interface MeResponse {
  user: {
    id: string;
    email: string;
    roles: UserRoleType[];
    status: string;
  };
}

@Controller()
export class UsersController {
  @Get('me')
  @UseGuards(AuthGuard)
  getMe(@Req() request: Request): MeResponse {
    const user = request.user!;
    return {
      user: {
        id: user.id,
        email: user.email,
        roles: user.roles,
        status: user.status,
      },
    };
  }
}
