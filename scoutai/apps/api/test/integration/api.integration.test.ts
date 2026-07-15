import 'reflect-metadata';
import { randomUUID } from 'node:crypto';
import { resolve } from 'node:path';
import { config as loadDotenv } from 'dotenv';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import type { INestApplication } from '@nestjs/common';
import { UserRoleType } from '@scoutai/database';
import { Argon2PasswordHasher } from '@scoutai/auth';
import { loadEnv, resetEnvCache } from '@scoutai/config';
import { getPrismaClient } from '@scoutai/database';
import request from 'supertest';
import { createNestApp } from '../../src/app.factory';

loadDotenv({ path: resolve(__dirname, '../../../../.env') });
resetEnvCache();
loadEnv();

const prisma = getPrismaClient();
const hasher = new Argon2PasswordHasher();
const testRunId = randomUUID().slice(0, 8);
const password = 'ValidPass1!';

function uniqueEmail(label: string): string {
  return `${label}-${testRunId}@integration.test`;
}

async function cleanupUsers(emails: string[]): Promise<void> {
  const normalizedEmails = emails.map((email) => email.trim().toLowerCase());
  if (normalizedEmails.length === 0) {
    return;
  }

  await prisma.user.deleteMany({
    where: {
      normalizedEmail: { in: normalizedEmails },
    },
  });
}

describe('API integration', () => {
  let app: INestApplication;
  const createdEmails: string[] = [];

  beforeAll(async () => {
    app = await createNestApp();
    await app.init();
  });

  afterAll(async () => {
    await cleanupUsers(createdEmails);
    await app.close();
    await prisma.$disconnect();
  });

  it('GET /health returns ok', async () => {
    const response = await request(app.getHttpServer()).get('/health').expect(200);

    expect(response.body).toEqual({
      status: 'ok',
      service: 'scoutai-api',
    });
  });

  it('GET /health/ready returns ok when dependencies are up', async () => {
    const response = await request(app.getHttpServer()).get('/health/ready').expect(200);

    expect(response.body.status).toBe('ok');
    expect(response.body.checks.postgres).toBe(true);
    expect(response.body.checks.redis).toBe(true);
  });

  it('POST /auth/register succeeds', async () => {
    const email = uniqueEmail('register');
    createdEmails.push(email);

    const response = await request(app.getHttpServer())
      .post('/auth/register')
      .send({ email, password })
      .expect(200);

    expect(response.body.user).toMatchObject({
      email: email.trim(),
      roles: [],
      status: 'ACTIVE',
    });
    expect(response.body.user.id).toBeTruthy();
    expect(response.body.user.passwordHash).toBeUndefined();
    expect(response.headers['set-cookie']).toBeDefined();
    expect(String(response.headers['set-cookie'])).toContain('HttpOnly');
  });

  it('POST /auth/register rejects duplicate email', async () => {
    const email = uniqueEmail('duplicate');
    createdEmails.push(email);

    await request(app.getHttpServer())
      .post('/auth/register')
      .send({ email, password })
      .expect(200);

    const response = await request(app.getHttpServer())
      .post('/auth/register')
      .send({ email, password })
      .expect(409);

    expect(response.body.error.code).toBe('EMAIL_ALREADY_EXISTS');
  });

  it('POST /auth/login rejects invalid credentials', async () => {
    const email = uniqueEmail('invalid-login');
    createdEmails.push(email);

    await request(app.getHttpServer())
      .post('/auth/register')
      .send({ email, password })
      .expect(200);

    const response = await request(app.getHttpServer())
      .post('/auth/login')
      .send({ email, password: 'WrongPass1!' })
      .expect(401);

    expect(response.body.error.code).toBe('INVALID_CREDENTIALS');
    expect(response.headers['set-cookie']).toBeUndefined();
  });

  it('POST /auth/login succeeds with valid credentials', async () => {
    const email = uniqueEmail('valid-login');
    createdEmails.push(email);

    await request(app.getHttpServer())
      .post('/auth/register')
      .send({ email, password })
      .expect(200);

    const response = await request(app.getHttpServer())
      .post('/auth/login')
      .send({ email, password })
      .expect(200);

    expect(response.body.user.email).toBe(email.trim());
    expect(response.headers['set-cookie']).toBeDefined();
  });

  it('GET /me rejects unauthenticated requests', async () => {
    const response = await request(app.getHttpServer()).get('/me').expect(401);

    expect(response.body.error.code).toBe('UNAUTHORIZED');
  });

  it('GET /me succeeds for authenticated user', async () => {
    const email = uniqueEmail('me-success');
    createdEmails.push(email);

    const agent = request.agent(app.getHttpServer());

    await agent.post('/auth/register').send({ email, password }).expect(200);

    const response = await agent.get('/me').expect(200);

    expect(response.body.user).toMatchObject({
      email: email.trim(),
      status: 'ACTIVE',
      roles: [],
    });
    expect(response.body.user.passwordHash).toBeUndefined();
  });

  it('POST /auth/logout invalidates session', async () => {
    const email = uniqueEmail('logout');
    createdEmails.push(email);

    const agent = request.agent(app.getHttpServer());

    await agent.post('/auth/register').send({ email, password }).expect(200);
    await agent.post('/auth/logout').expect(200);
    await agent.get('/me').expect(401);
  });

  it('GET /admin/system-info rejects non-admin users', async () => {
    const email = uniqueEmail('non-admin');
    createdEmails.push(email);

    const agent = request.agent(app.getHttpServer());
    await agent.post('/auth/register').send({ email, password }).expect(200);

    const response = await agent.get('/admin/system-info').expect(403);
    expect(response.body.error.code).toBe('FORBIDDEN');
  });

  it('GET /admin/system-info succeeds for admin users', async () => {
    const email = uniqueEmail('admin');
    createdEmails.push(email);
    const normalizedEmail = email.trim().toLowerCase();
    const passwordHash = await hasher.hash(password);

    const adminUser = await prisma.user.create({
      data: {
        email,
        normalizedEmail,
        passwordHash,
        status: 'ACTIVE',
        roles: {
          create: [{ role: UserRoleType.SCOUTAI_ADMIN }],
        },
      },
    });

    const agent = request.agent(app.getHttpServer());
    await agent.post('/auth/login').send({ email, password }).expect(200);

    const response = await agent.get('/admin/system-info').expect(200);

    expect(response.body).toMatchObject({
      service: 'scoutai-api',
      environment: expect.any(String),
      nodeVersion: expect.any(String),
      timestamp: expect.any(String),
    });

    await prisma.user.delete({ where: { id: adminUser.id } });
    const index = createdEmails.indexOf(email);
    if (index >= 0) {
      createdEmails.splice(index, 1);
    }
  });
});
