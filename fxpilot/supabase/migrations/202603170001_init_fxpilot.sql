create extension if not exists "pgcrypto";

create table if not exists profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  display_name text not null default 'Trader',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists broker_credentials (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  api_key text not null,
  account_id text not null,
  broker_name text not null default 'oanda',
  is_practice boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, broker_name)
);

create table if not exists watchlists (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  pair text not null,
  created_at timestamptz not null default now(),
  unique (user_id, pair)
);

create table if not exists trade_history (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  pair text not null,
  direction text not null check (direction in ('BUY', 'SELL')),
  units integer not null,
  open_price numeric not null,
  close_price numeric,
  open_time timestamptz not null default now(),
  close_time timestamptz,
  profit_loss numeric not null default 0,
  status text not null default 'OPEN',
  stop_loss numeric,
  take_profit numeric,
  broker_trade_id text,
  beast_mode boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists autopilot_settings (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references auth.users(id) on delete cascade,
  enabled boolean not null default false,
  pairs text[] not null default array['EUR_USD'],
  interval_minutes integer not null default 5,
  risk_level text not null default 'moderate',
  base_units integer not null default 5000,
  max_units integer not null default 20000,
  max_unit_cap integer not null default 50000,
  daily_loss_limit numeric not null default 1000,
  max_open_trades integer not null default 4,
  cooldown_minutes integer not null default 10,
  paper_mode boolean not null default true,
  adaptive_enabled boolean not null default true,
  profit_compound_pct numeric not null default 20,
  beast_mode_enabled boolean not null default false,
  beast_mode_active boolean not null default false,
  beast_mode_max_units integer not null default 35000,
  beast_mode_consensus_min numeric not null default 0.75,
  beast_mode_min_rr numeric not null default 1.8,
  beast_mode_tp_multiplier numeric not null default 1.3,
  beast_mode_compound_pct numeric not null default 30,
  beast_mode_max_open_trades integer not null default 2,
  beast_mode_auto boolean not null default false,
  beast_mode_reason text
);

create table if not exists autopilot_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  pair text not null,
  action text not null check (action in ('BUY', 'SELL', 'HOLD')),
  reason text not null,
  units integer not null default 0,
  executed boolean not null default false,
  error text,
  created_at timestamptz not null default now()
);

create table if not exists autopilot_reasoning (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  cycle_id text not null,
  pair text not null,
  technical_vote text,
  technical_confidence numeric,
  technical_reasoning text,
  technical_indicators jsonb,
  sentiment_vote text,
  sentiment_confidence numeric,
  sentiment_reasoning text,
  sentiment_headlines jsonb,
  risk_vote text,
  risk_confidence numeric,
  risk_reasoning text,
  risk_metrics jsonb,
  final_action text,
  confidence numeric,
  final_reasoning text,
  consensus_score numeric,
  executed boolean not null default false,
  units integer,
  entry_price numeric,
  stop_loss numeric,
  take_profit numeric,
  broker_trade_id text,
  created_at timestamptz not null default now()
);

create table if not exists benched_pairs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  pair text not null,
  reason text not null,
  status text not null default 'benched',
  win_rate numeric,
  total_pnl numeric,
  trades_count integer not null default 0,
  benched_at timestamptz not null default now(),
  review_after timestamptz,
  reinstated_at timestamptz,
  probe_trade_id text,
  probe_result text,
  unique (user_id, pair)
);

create table if not exists paper_accounts (
  user_id uuid primary key references auth.users(id) on delete cascade,
  balance numeric not null default 100000,
  initial_balance numeric not null default 100000,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists paper_trades (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  pair text not null,
  direction text not null,
  units integer not null,
  open_price numeric not null,
  close_price numeric,
  open_time timestamptz not null default now(),
  close_time timestamptz,
  profit_loss numeric not null default 0,
  status text not null default 'OPEN',
  stop_loss numeric,
  take_profit numeric,
  trailing_stop_distance numeric
);

create table if not exists price_alerts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  pair text not null,
  target_price numeric not null,
  direction text not null check (direction in ('above', 'below')),
  triggered boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists telegram_settings (
  user_id uuid primary key references auth.users(id) on delete cascade,
  bot_token text not null,
  chat_id text not null,
  enabled boolean not null default false,
  alert_on_trade boolean not null default true,
  alert_on_autopilot boolean not null default true,
  alert_on_price_alert boolean not null default true
);

create table if not exists tradingview_webhooks (
  user_id uuid primary key references auth.users(id) on delete cascade,
  webhook_token text not null,
  enabled boolean not null default false,
  default_units integer not null default 5000
);

create table if not exists trader_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  display_name text not null,
  avatar_emoji text default '📈',
  bio text default '',
  is_public boolean not null default false,
  win_rate numeric not null default 0,
  total_pnl numeric not null default 0,
  total_trades integer not null default 0,
  followers_count integer not null default 0
);

create table if not exists shared_strategies (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  description text not null default '',
  pairs text[] not null default array['EUR_USD'],
  timeframe text not null default 'M15',
  risk_level text not null default 'moderate',
  entry_rules text not null default '',
  exit_rules text not null default '',
  likes_count integer not null default 0,
  created_at timestamptz not null default now()
);

create table if not exists copy_relationships (
  id uuid primary key default gen_random_uuid(),
  leader_id uuid not null references auth.users(id) on delete cascade,
  follower_id uuid not null references auth.users(id) on delete cascade,
  active boolean not null default true,
  copy_multiplier numeric not null default 1,
  created_at timestamptz not null default now(),
  unique (leader_id, follower_id)
);

alter table profiles enable row level security;
alter table broker_credentials enable row level security;
alter table watchlists enable row level security;
alter table trade_history enable row level security;
alter table autopilot_settings enable row level security;
alter table autopilot_logs enable row level security;
alter table autopilot_reasoning enable row level security;
alter table benched_pairs enable row level security;
alter table paper_accounts enable row level security;
alter table paper_trades enable row level security;
alter table price_alerts enable row level security;
alter table telegram_settings enable row level security;
alter table tradingview_webhooks enable row level security;
alter table trader_profiles enable row level security;
alter table shared_strategies enable row level security;
alter table copy_relationships enable row level security;

create policy "users own profiles" on profiles for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users own broker creds" on broker_credentials for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users own watchlists" on watchlists for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users own trade history" on trade_history for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users own autopilot settings" on autopilot_settings for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users own autopilot logs" on autopilot_logs for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users own autopilot reasoning" on autopilot_reasoning for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users own benched pairs" on benched_pairs for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users own paper accounts" on paper_accounts for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users own paper trades" on paper_trades for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users own price alerts" on price_alerts for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users own telegram settings" on telegram_settings for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users own webhook settings" on tradingview_webhooks for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users own trader profiles" on trader_profiles for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users own shared strategies" on shared_strategies for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users own copy relationships" on copy_relationships
for all
using (auth.uid() = leader_id or auth.uid() = follower_id)
with check (auth.uid() = leader_id or auth.uid() = follower_id);
