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

export type WorkerTemplateRead = {
  id: string;
  workspace_id?: string | null;
  creator_user_id?: string | null;
  name: string;
  slug?: string | null;
  template_key: string;
  display_name: string;
  short_description?: string | null;
  description?: string | null;
  category: string;
  worker_type: string;
  worker_category: string;
  plan_version: string;
  visibility: "private" | "workspace" | "public" | "marketplace";
  status: "draft" | "active" | "archived";
  instructions?: string | null;
  model_name?: string | null;
  config_json?: Record<string, unknown> | null;
  capabilities_json?: Record<string, unknown> | null;
  actions_json?: string[] | null;
  tools_json?: string[] | null;
  memory_enabled: boolean;
  chain_enabled: boolean;
  is_system_template: boolean;
  is_public: boolean;
  is_marketplace_listed: boolean;
  is_active: boolean;
  pricing_type: "free" | "subscription" | "one_time" | "internal";
  price_cents: number;
  currency: string;
  install_count: number;
  rating_avg: number;
  rating_count: number;
  tags_json?: string[] | null;
  created_at: string;
  updated_at: string;
};

export type WorkerTemplateCatalogRead = {
  id: string;
  slug?: string | null;
  name: string;
  display_name: string;
  short_description?: string | null;
  description?: string | null;
  category: string;
  worker_type: string;
  worker_category: string;
  visibility: "private" | "workspace" | "public" | "marketplace";
  status: "draft" | "active" | "archived";
  is_marketplace_listed: boolean;
  pricing_type: "free" | "subscription" | "one_time" | "internal";
  price_cents: number;
  currency: string;
  install_count: number;
  rating_avg: number;
  rating_count: number;
  tags_json?: string[] | null;
};

export type WorkerToolRead = {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  category: string;
  config_schema_json?: Record<string, unknown> | null;
  is_system: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type WorkerToolCatalogRead = {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  category: string;
};

export type WorkerToolListResponse = {
  items: WorkerToolRead[];
  total: number;
};

export type WorkerInstanceRead = {
  id: string;
  workspace_id: string;
  template_id: string;
  owner_user_id?: string | null;
  legacy_worker_id?: string | null;
  name: string;
  status: "active" | "paused" | "disabled" | "error";
  runtime_config_json?: Record<string, unknown> | null;
  last_run_at?: string | null;
  next_run_at?: string | null;
  schedule_expression?: string | null;
  memory_scope: "none" | "instance" | "workspace";
  created_at: string;
  updated_at: string;
};

export type WorkerInstanceExecuteResponse = {
  success: boolean;
  queued: boolean;
  run_id: string;
  task_id?: string | null;
  status: "queued" | "running" | "completed" | "failed" | "paused";
};

export type PlatformWorkerRunRead = {
  id: string;
  workspace_id?: string | null;
  worker_id: string;
  instance_id?: string | null;
  template_id?: string | null;
  campaign_id?: string | null;
  run_type: string;
  triggered_by: "manual" | "schedule" | "api" | "chain" | "event";
  trigger_source?: string | null;
  started_at: string;
  finished_at?: string | null;
  status: "queued" | "running" | "completed" | "failed" | "paused";
  attempts: number;
  input_json?: Record<string, unknown> | null;
  output_json?: Record<string, unknown> | null;
  summary?: string | null;
  duration_ms?: number | null;
  error_message?: string | null;
  token_usage_input: number;
  token_usage_output: number;
  cost_cents: number;
  created_at?: string | null;
  error_text?: string | null;
};

export type WorkerRunListResponse = {
  items: PlatformWorkerRunRead[];
  total: number;
};

export type WorkerChainStepRead = {
  id: string;
  chain_id: string;
  step_order: number;
  worker_instance_id?: string | null;
  worker_template_id?: string | null;
  step_name: string;
  input_mapping_json?: Record<string, unknown> | null;
  condition_json?: Record<string, unknown> | null;
  on_success_next_step?: number | null;
  on_failure_next_step?: number | null;
  created_at: string;
  updated_at: string;
};

export type WorkerChainRead = {
  id: string;
  workspace_id: string;
  name: string;
  description?: string | null;
  status: "draft" | "active" | "paused" | "archived";
  trigger_type: "manual" | "schedule" | "event" | "api";
  trigger_config_json?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  steps: WorkerChainStepRead[];
};

export type WorkerChainListResponse = {
  items: WorkerChainRead[];
  total: number;
};

export type WorkerChainStepExecutionRead = {
  step_order: number;
  status: string;
  run_id?: string | null;
  worker_instance_id?: string | null;
  worker_template_id?: string | null;
  summary?: string | null;
  error?: string | null;
  next_step_order?: number | null;
  skipped_reason?: string | null;
};

export type WorkerChainRunResponse = {
  success: boolean;
  chain_id: string;
  chain_run_id: string;
  status: string;
  executed_steps: WorkerChainStepExecutionRead[];
  total_steps_executed: number;
  final_output: Record<string, unknown>;
};

export type WorkerSubscriptionRead = {
  id: string;
  workspace_id: string;
  worker_template_id: string;
  purchaser_user_id?: string | null;
  billing_status: string;
  price_cents: number;
  currency: string;
  started_at: string;
  ends_at?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type WorkerReviewRead = {
  id: string;
  rating: number;
  review_text?: string | null;
  created_at: string;
};

export type MarketplaceListingRead = {
  template: WorkerTemplateCatalogRead;
  is_installed: boolean;
  subscription?: WorkerSubscriptionRead | null;
};

export type MarketplaceWorkerDetailRead = {
  template: WorkerTemplateCatalogRead;
  is_installed: boolean;
  subscription?: WorkerSubscriptionRead | null;
  reviews: WorkerReviewRead[];
  tools: WorkerToolCatalogRead[];
  average_rating: number;
  installs: number;
};

export type MarketplaceInstallResponse = {
  success: boolean;
  worker_template_id: string;
  subscription: WorkerSubscriptionRead;
  message: string;
};

export type PublicWorkerListItem = {
  id: string;
  slug: string;
  name: string;
  short_description?: string | null;
  category: string;
  pricing_type: "free" | "subscription" | "one_time" | "internal";
  price_cents: number;
  currency: string;
  rating_avg: number;
  rating_count: number;
  install_count: number;
  tags_json?: string[] | null;
};

export type PublicWorkerDetailRead = {
  template: WorkerTemplateCatalogRead;
  reviews: WorkerReviewRead[];
  tools: WorkerToolCatalogRead[];
  average_rating: number;
  installs: number;
};

export type WorkerDraftRead = {
  id: string;
  workspace_id: string;
  creator_user_id: string;
  published_template_id: string | null;
  name: string;
  slug: string;
  description: string | null;
  category: string;
  prompt_template: string;
  input_schema_json: Record<string, unknown> | null;
  output_schema_json: Record<string, unknown> | null;
  tools_json: Array<{ label: string; enabled: boolean; config?: Record<string, unknown> }> | null;
  visibility: "private" | "workspace" | "public" | "marketplace";
  price_monthly: number | null;
  price_onetime: number | null;
  icon: string | null;
  screenshots_json: string[] | null;
  tags_json: string[] | null;
  usage_examples_json: Array<Record<string, unknown>> | null;
  is_published: boolean;
  creator_revenue_percent: number;
  platform_revenue_percent: number;
  created_at: string;
  updated_at: string;
};

export type WorkerDraftListResponse = {
  items: WorkerDraftRead[];
  total: number;
};

export type WorkerDraftCreateResponse = {
  worker_draft_id: string;
  draft: WorkerDraftRead;
};

export type WorkerDraftTestResponse = {
  worker_draft_id: string;
  run_id: string;
  status: string;
  rendered_prompt: string;
  execution_result: Record<string, unknown>;
  normalized_output: Record<string, unknown>;
};

export type WorkerDraftPublishResponse = {
  worker_draft_id: string;
  published_template_id: string;
  is_published: boolean;
  template: WorkerTemplateRead;
};
