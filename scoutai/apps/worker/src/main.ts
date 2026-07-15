import { config } from 'dotenv';
import { resolve } from 'node:path';
import { Queue, Worker, type ConnectionOptions, type Job } from 'bullmq';
import Redis from 'ioredis';
import { loadEnv } from '@scoutai/config';
import { createLogger } from '@scoutai/observability';

config({ path: resolve(process.cwd(), '../../.env') });

export const SYSTEM_QUEUE = 'scoutai-system';
export const SMOKE_JOB_NAME = 'system.smoke';

const logger = createLogger({ service: 'scoutai-worker' });

export function getRedisConnectionOptions(): ConnectionOptions {
  const env = loadEnv();
  return {
    url: env.REDIS_URL,
    maxRetriesPerRequest: null,
  };
}

export function createRedisConnection(): Redis {
  const env = loadEnv();
  return new Redis(env.REDIS_URL, { maxRetriesPerRequest: null });
}

export async function processSmokeJob(job: Job): Promise<{ ok: true }> {
  if (job.name !== SMOKE_JOB_NAME) {
    throw new Error(`Unexpected job name: ${job.name}`);
  }

  logger.info('system.smoke job completed', {
    event: 'job.completed',
    jobName: job.name,
    jobId: job.id,
    payload: job.data,
  });

  return { ok: true };
}

export function createSmokeWorker(connection: ConnectionOptions = getRedisConnectionOptions()): Worker {
  return new Worker(SYSTEM_QUEUE, processSmokeJob, { connection });
}

export async function enqueueSmokeJob(
  payload: Record<string, unknown> = {},
  connection: ConnectionOptions = getRedisConnectionOptions(),
): Promise<string | undefined> {
  const queue = new Queue(SYSTEM_QUEUE, { connection });

  try {
    const job = await queue.add(SMOKE_JOB_NAME, payload);
    return job.id;
  } finally {
    await queue.close();
  }
}

async function main(): Promise<void> {
  loadEnv();
  const connection = createRedisConnection();
  const worker = createSmokeWorker();

  worker.on('failed', (job, error) => {
    logger.error('Job failed', {
      event: 'job.failed',
      jobId: job?.id,
      jobName: job?.name,
      error: error.message,
    });
  });

  logger.info('Worker started', {
    event: 'worker.started',
    queue: SYSTEM_QUEUE,
    jobName: SMOKE_JOB_NAME,
  });

  const shutdown = async (): Promise<void> => {
    logger.info('Worker shutting down', { event: 'worker.shutdown' });
    await worker.close();
    await connection.quit();
    process.exit(0);
  };

  process.on('SIGINT', () => {
    void shutdown();
  });
  process.on('SIGTERM', () => {
    void shutdown();
  });
}

if (require.main === module) {
  main().catch((error: unknown) => {
    console.error(error);
    process.exit(1);
  });
}
