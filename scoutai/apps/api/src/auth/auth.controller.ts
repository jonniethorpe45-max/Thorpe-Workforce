import { Body, Controller, HttpCode, Inject, Post, Req, Res, UseGuards } from '@nestjs/common';
import { getEnv } from '@scoutai/config';
import type { Request, Response } from 'express';
import {
  loginRequestSchema,
  registerRequestSchema,
  type LoginRequestInput,
  type RegisterRequestInput,
} from '@scoutai/validation';
import { RateLimitGuard } from '../common/rate-limit.guard';
import { ZodValidationPipe } from '../common/zod-validation.pipe';
import { AuthGuard } from './auth.guard';
import { AuthService } from './auth.service';
import { SessionService } from './session.service';

function getClientMeta(request: Request) {
  const forwarded = request.headers['x-forwarded-for'];
  const ipAddress =
    typeof forwarded === 'string'
      ? forwarded.split(',')[0]?.trim()
      : request.ip ?? request.socket.remoteAddress ?? undefined;
  const userAgent =
    typeof request.headers['user-agent'] === 'string'
      ? request.headers['user-agent']
      : undefined;

  return { ipAddress, userAgent };
}

@Controller('auth')
export class AuthController {
  constructor(
    @Inject(AuthService) private readonly authService: AuthService,
    @Inject(SessionService) private readonly sessionService: SessionService,
  ) {}

  @Post('register')
  @HttpCode(200)
  @UseGuards(RateLimitGuard)
  async register(
    @Body(new ZodValidationPipe(registerRequestSchema)) body: RegisterRequestInput,
    @Req() request: Request,
    @Res({ passthrough: true }) response: Response,
  ) {
    const meta = getClientMeta(request);
    const result = await this.authService.register({
      email: body.email,
      password: body.password,
      requestId: request.requestId,
      ...meta,
    });

    this.sessionService.setSessionCookie(response, result.sessionToken);
    return { user: result.user };
  }

  @Post('login')
  @HttpCode(200)
  @UseGuards(RateLimitGuard)
  async login(
    @Body(new ZodValidationPipe(loginRequestSchema)) body: LoginRequestInput,
    @Req() request: Request,
    @Res({ passthrough: true }) response: Response,
  ) {
    const meta = getClientMeta(request);
    const result = await this.authService.login({
      email: body.email,
      password: body.password,
      requestId: request.requestId,
      ...meta,
    });

    this.sessionService.setSessionCookie(response, result.sessionToken);
    return { user: result.user };
  }

  @Post('logout')
  @HttpCode(200)
  @UseGuards(AuthGuard)
  async logout(@Req() request: Request, @Res({ passthrough: true }) response: Response) {
    const env = getEnv();
    const rawToken =
      request.cookies?.[env.SESSION_COOKIE_NAME] ??
      this.sessionService.readSessionToken(request.headers.cookie, env.SESSION_COOKIE_NAME);

    await this.authService.logout({
      rawToken,
      requestId: request.requestId,
      actorId: request.user?.id,
    });

    this.sessionService.clearSessionCookie(response);
    return { ok: true };
  }
}
