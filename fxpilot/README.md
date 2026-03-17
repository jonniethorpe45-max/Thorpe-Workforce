# FXPilot

Production-grade AI-powered forex trading dashboard foundation built with:

- React 18 + Vite + TypeScript
- Tailwind CSS + shadcn/ui-style components
- Supabase (Auth, Postgres, Realtime, Edge Functions)
- React Query + Recharts + Framer Motion + Sonner
- PWA support (`vite-plugin-pwa`)

## Local run

```bash
cd fxpilot
npm install
cp .env.example .env
npm run dev
```

## Scripts

- `npm run dev` – start Vite dev server
- `npm run build` – type-check + production build
- `npm run test` – unit tests (Vitest)
- `npm run test:e2e` – Playwright tests

## Supabase

- SQL migration: `supabase/migrations/202603170001_init_fxpilot.sql`
- Edge functions:
  - `oanda-proxy`
  - `autopilot`
  - `ai-analysis`
  - `news-sentiment`
  - `telegram-alert`
  - `tradingview-webhook`

Deploy functions with Supabase CLI, then set frontend env:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

When env variables are missing, the app runs in local mock mode so UI and tests remain usable.
