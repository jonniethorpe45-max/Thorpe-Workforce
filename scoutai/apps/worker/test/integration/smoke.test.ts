import { config } from 'dotenv';
import { resolve } from 'node:path';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { Queue, QueueEvents } from 'bullmq';
import Redis from 'ioredis';
import {
  createRedisConnection,
  createSmokeWorker,
  enqueueSmokeJob,
  getRedisConnectionOptions,
  SMOKE_JOB_NAME,
  SYSTEM_QUEUE,
} from '../../src/main';

config({ path: resolve(process.cwd(), '../../.env') });

describe('system.smoke integration', () => {
  const connectionOptions = getRedisConnectionOptions();
  let connection: Redis;
  let worker: ReturnType<typeof createSmokeWorker>;
  let queue: Queue;
  let queueEvents: QueueEvents;
  let redisAvailable = false;

  beforeAll(async () => {
    try {
      connection = createRedisConnection();
      await connection.ping();
      redisAvailable = true;
      worker = createSmokeWorker(connectionOptions);
      queue = new Queue(SYSTEM_QUEUE, { connection: connectionOptions });
      queueEvents = new QueueEvents(SYSTEM_QUEUE, { connection: connectionOptions });
      await queueEvents.waitUntilReady();
    } catch {
      redisAvailable = false;
    }
  });

  afterAll(async () => {
    if (!redisAvailable) {
      return;
    }
    await queue.close();
    await queueEvents.close();
    await worker.close();
    await connection.quit();
  });

  it('enqueues and completes a system.smoke job via enqueueSmokeJob', async () => {
    if (!redisAvailable) {
      return;
    }

    const jobId = await enqueueSmokeJob({ test: true }, connectionOptions);
    expect(jobId).toBeDefined();

    const job = await queue.getJob(jobId!);
    expect(job).toBeDefined();

    const result = await job!.waitUntilFinished(queueEvents, 15_000);
    expect(result).toEqual({ ok: true });
  });

  it('processes inline jobs with Worker events', async () => {
    if (!redisAvailable) {
      return;
    }

    const job = await queue.add(SMOKE_JOB_NAME, { marker: 'integration' });
    const result = await job.waitUntilFinished(queueEvents, 15_000);
    expect(result).toEqual({ ok: true });
  });
});
