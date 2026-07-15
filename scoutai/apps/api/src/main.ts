import 'reflect-metadata';
import { getEnv } from '@scoutai/config';
import { createNestApp } from './app.factory';

async function bootstrap(): Promise<void> {
  const app = await createNestApp();
  const env = getEnv();

  await app.listen(env.API_PORT);
  console.log(`ScoutAI API listening on port ${env.API_PORT}`);
}

bootstrap().catch((error) => {
  console.error(error);
  process.exit(1);
});
