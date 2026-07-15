import 'reflect-metadata';
import { resolve } from 'node:path';
import { config as loadDotenv } from 'dotenv';
import { INestApplication } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import cookieParser from 'cookie-parser';
import { getEnv, loadEnv } from '@scoutai/config';
import { AppModule } from './app.module';
import { HttpExceptionFilter } from './common/http-exception.filter';

export function loadRootEnv(): void {
  loadDotenv({ path: resolve(__dirname, '../../.env') });
}

export async function createNestApp(): Promise<INestApplication> {
  loadRootEnv();
  loadEnv();

  const app = await NestFactory.create(AppModule, {
    bufferLogs: true,
  });

  const env = getEnv();

  app.enableCors({
    origin: env.APP_URL,
    credentials: true,
  });

  app.use(cookieParser());
  app.useGlobalFilters(new HttpExceptionFilter());

  return app;
}
