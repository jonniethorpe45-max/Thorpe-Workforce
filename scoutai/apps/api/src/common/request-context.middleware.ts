import { Injectable, NestMiddleware } from '@nestjs/common';
import type { NextFunction, Request, Response } from 'express';
import { createLogger, createRequestId } from '@scoutai/observability';

const baseLogger = createLogger({ service: 'scoutai-api' });

@Injectable()
export class RequestContextMiddleware implements NestMiddleware {
  use(req: Request, res: Response, next: NextFunction): void {
    const requestId =
      (typeof req.headers['x-request-id'] === 'string' && req.headers['x-request-id'].trim()) ||
      createRequestId();

    req.requestId = requestId;
    req.logger = {
      debug: (message, context) => baseLogger.debug(message, { requestId, ...context }),
      info: (message, context) => baseLogger.info(message, { requestId, ...context }),
      warn: (message, context) => baseLogger.warn(message, { requestId, ...context }),
      error: (message, context) => baseLogger.error(message, { requestId, ...context }),
    };

    res.setHeader('x-request-id', requestId);
    next();
  }
}
