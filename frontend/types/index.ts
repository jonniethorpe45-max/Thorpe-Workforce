export type Worker = {
  id: string;
  name: string;
  worker_type: string;
  worker_category: string;
  mission: string;
  goal: string;
  plan_version: string;
  allowed_actions?: string[] | null;
  template_id?: string | null;
  origin_type: string;
  is_custom_worker: boolean;
  is_internal: boolean;
  status: string;
  tone: string;
  send_limit_per_day: number;
  run_interval_minutes: number;
  last_run_at?: string | null;
  next_run_at?: string | null;
  last_error_text?: string | null;
};

export type Campaign = {
  id: string;
  name: string;
  status: string;
  worker_id?: string | null;
  target_industry?: string;
  target_roles?: string[];
  target_locations?: string[];
};

export type WorkerRun = {
  id: string;
  worker_id: string;
  campaign_id?: string | null;
  run_type: string;
  started_at: string;
  finished_at?: string | null;
  status: string;
  attempts: number;
  input_json?: Record<string, unknown> | null;
  output_json?: Record<string, unknown> | null;
  error_text?: string | null;
};

export type Lead = {
  id: string;
  company_name: string;
  full_name?: string;
  title?: string;
  email: string;
  lead_status: string;
  location?: string;
};

export type Reply = {
  id: string;
  reply_text: string;
  intent_classification: string;
  requires_human_review: boolean;
  created_at: string;
};

export type Meeting = {
  id: string;
  lead_id: string;
  calendar_provider: string;
  scheduled_start: string;
  scheduled_end: string;
  meeting_status: string;
};
