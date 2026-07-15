import { randomUUID } from 'node:crypto';

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LoggerOptions {
  service: string;
}

export interface LogContext {
  requestId?: string;
  event?: string;
  userId?: string;
  [key: string]: unknown;
}

export interface Logger {
  debug(message: string, context?: LogContext): void;
  info(message: string, context?: LogContext): void;
  warn(message: string, context?: LogContext): void;
  error(message: string, context?: LogContext): void;
}

const SENSITIVE_KEY_PATTERN =
  /(password|passwd|secret|token|authorization|api[-_]?key|credential)/i;

function isSensitiveKey(key: string): boolean {
  return SENSITIVE_KEY_PATTERN.test(key);
}

function sanitizeValue(value: unknown): unknown {
  if (value === null || value === undefined) {
    return value;
  }
  if (Array.isArray(value)) {
    return value.map((item) => sanitizeValue(item));
  }
  if (typeof value === 'object') {
    return sanitizeRecord(value as Record<string, unknown>);
  }
  return value;
}

export function sanitizeRecord(record: Record<string, unknown>): Record<string, unknown> {
  const sanitized: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(record)) {
    if (isSensitiveKey(key)) {
      sanitized[key] = '[REDACTED]';
      continue;
    }
    sanitized[key] = sanitizeValue(value);
  }
  return sanitized;
}

export interface SerializedError {
  name: string;
  message: string;
  stack?: string;
  cause?: SerializedError;
}

export function serializeError(error: unknown): SerializedError {
  if (error instanceof Error) {
    const serialized: SerializedError = {
      name: error.name,
      message: error.message,
    };
    if (error.stack) {
      serialized.stack = error.stack;
    }
    if (error.cause !== undefined) {
      serialized.cause = serializeError(error.cause);
    }
    return serialized;
  }
  return {
    name: 'UnknownError',
    message: String(error),
  };
}

export function createRequestId(): string {
  return randomUUID();
}

function writeLog(
  level: LogLevel,
  service: string,
  message: string,
  context: LogContext = {},
): void {
  const { requestId, event, userId, ...rest } = context;
  const payload: Record<string, unknown> = {
    timestamp: new Date().toISOString(),
    level,
    service,
    message,
  };
  if (requestId) {
    payload.requestId = requestId;
  }
  if (event) {
    payload.event = event;
  }
  if (userId) {
    payload.userId = userId;
  }
  if (Object.keys(rest).length > 0) {
    payload.context = sanitizeRecord(rest);
  }
  const line = JSON.stringify(payload);
  if (level === 'error') {
    console.error(line);
    return;
  }
  if (level === 'warn') {
    console.warn(line);
    return;
  }
  console.log(line);
}

export function createLogger(options: LoggerOptions): Logger {
  const { service } = options;
  return {
    debug(message, context) {
      writeLog('debug', service, message, context);
    },
    info(message, context) {
      writeLog('info', service, message, context);
    },
    warn(message, context) {
      writeLog('warn', service, message, context);
    },
    error(message, context) {
      writeLog('error', service, message, context);
    },
  };
}
