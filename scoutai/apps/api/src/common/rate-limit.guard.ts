import {
  CanActivate,
  ExecutionContext,
  HttpException,
  HttpStatus,
  Injectable,
} from '@nestjs/common';
import type { Request } from 'express';

/**
 * Simple in-memory rate limiter for auth endpoints.
 *
 * Limits register and login to 20 requests per 15 minutes per client IP.
 * This is a Stage 3 foundation — replace with a Redis-backed sliding window
 * (e.g. ioredis + BullMQ or dedicated rate-limit store) before production scale.
 */
const WINDOW_MS = 15 * 60 * 1000;
const MAX_REQUESTS = 20;

interface RateLimitEntry {
  count: number;
  windowStart: number;
}

const store = new Map<string, RateLimitEntry>();

function getClientIp(request: Request): string {
  const forwarded = request.headers['x-forwarded-for'];
  if (typeof forwarded === 'string' && forwarded.length > 0) {
    return forwarded.split(',')[0]?.trim() ?? request.ip ?? 'unknown';
  }
  return request.ip ?? request.socket.remoteAddress ?? 'unknown';
}

@Injectable()
export class RateLimitGuard implements CanActivate {
  canActivate(context: ExecutionContext): boolean {
    const request = context.switchToHttp().getRequest<Request>();
    const ip = getClientIp(request);
    const now = Date.now();
    const key = `auth:${ip}`;

    const entry = store.get(key);
    if (!entry || now - entry.windowStart >= WINDOW_MS) {
      store.set(key, { count: 1, windowStart: now });
      return true;
    }

    if (entry.count >= MAX_REQUESTS) {
      throw new HttpException(
        {
          code: 'RATE_LIMITED',
          message: 'Too many requests. Please try again later.',
        },
        HttpStatus.TOO_MANY_REQUESTS,
      );
    }

    entry.count += 1;
    store.set(key, entry);
    return true;
  }
}
