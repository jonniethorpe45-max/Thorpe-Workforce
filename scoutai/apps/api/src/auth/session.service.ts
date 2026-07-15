import { Inject, Injectable } from '@nestjs/common';
import { getEnv } from '@scoutai/config';
import type { Prisma } from '@scoutai/database';
import type { Response } from 'express';
import { PrismaService } from '../database/prisma.service';
import { generateSessionToken, hashSessionToken } from './auth.utils';

export interface SessionCreationResult {
  rawToken: string;
  sessionId: string;
  expiresAt: Date;
}

type ValidSession = Prisma.SessionGetPayload<{
  include: {
    user: {
      include: { roles: true };
    };
  };
}>;

@Injectable()
export class SessionService {
  constructor(@Inject(PrismaService) private readonly prisma: PrismaService) {}

  async createSession(
    userId: string,
    options: { ipAddress?: string; userAgent?: string } = {},
  ): Promise<SessionCreationResult> {
    const env = getEnv();
    const rawToken = generateSessionToken();
    const tokenHash = hashSessionToken(rawToken);
    const expiresAt = new Date(Date.now() + env.SESSION_TTL_SECONDS * 1000);

    const session = await this.prisma.client.session.create({
      data: {
        userId,
        tokenHash,
        expiresAt,
        ipAddress: options.ipAddress ?? null,
        userAgent: options.userAgent ?? null,
      },
    });

    return { rawToken, sessionId: session.id, expiresAt };
  }

  setSessionCookie(response: Response, rawToken: string): void {
    const env = getEnv();
    response.cookie(env.SESSION_COOKIE_NAME, rawToken, {
      httpOnly: true,
      secure: env.COOKIE_SECURE,
      sameSite: env.COOKIE_SAMESITE,
      maxAge: env.SESSION_TTL_SECONDS * 1000,
      path: '/',
    });
  }

  clearSessionCookie(response: Response): void {
    const env = getEnv();
    response.clearCookie(env.SESSION_COOKIE_NAME, {
      httpOnly: true,
      secure: env.COOKIE_SECURE,
      sameSite: env.COOKIE_SAMESITE,
      path: '/',
    });
  }

  readSessionToken(cookieHeader: string | undefined, cookieName: string): string | null {
    if (!cookieHeader) {
      return null;
    }

    const cookies = cookieHeader.split(';');
    for (const part of cookies) {
      const [name, ...rest] = part.trim().split('=');
      if (name === cookieName) {
        const value = rest.join('=');
        return value.length > 0 ? decodeURIComponent(value) : null;
      }
    }
    return null;
  }

  async findValidSession(rawToken: string): Promise<ValidSession | null> {
    const tokenHash = hashSessionToken(rawToken);
    const now = new Date();

    return this.prisma.client.session.findFirst({
      where: {
        tokenHash,
        revokedAt: null,
        expiresAt: { gt: now },
      },
      include: {
        user: {
          include: { roles: true },
        },
      },
    });
  }

  async revokeSession(rawToken: string): Promise<boolean> {
    const tokenHash = hashSessionToken(rawToken);
    const session = await this.prisma.client.session.findFirst({
      where: { tokenHash, revokedAt: null },
    });

    if (!session) {
      return false;
    }

    await this.prisma.client.session.update({
      where: { id: session.id },
      data: { revokedAt: new Date() },
    });

    return true;
  }
}
