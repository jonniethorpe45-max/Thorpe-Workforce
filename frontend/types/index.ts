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
  is_featured: boolean;
  featured_rank: number;
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
  is_featured: boolean;
  featured_rank: number;
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
  has_active_entitlement: boolean;
  purchase_required: boolean;
  subscription?: WorkerSubscriptionRead | null;
};

export type MarketplaceWorkerDetailRead = {
  template: WorkerTemplateCatalogRead;
  is_installed: boolean;
  has_active_entitlement: boolean;
  purchase_required: boolean;
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
  is_featured: boolean;
  featured_rank: number;
  tags_json?: string[] | null;
  created_at?: string | null;
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

export type BillingPlanRead = {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  monthly_price_cents: number;
  annual_price_cents?: number | null;
  max_worker_drafts?: number | null;
  max_published_workers?: number | null;
  max_worker_installs_per_workspace?: number | null;
  max_worker_runs_per_month?: number | null;
  allow_worker_builder: boolean;
  allow_marketplace_publishing: boolean;
  allow_private_workers: boolean;
  allow_public_workers: boolean;
  allow_marketplace_install: boolean;
  allow_team_features: boolean;
  is_active: boolean;
};

export type BillingSubscriptionRead = {
  id: string;
  workspace_id: string;
  plan_id?: string | null;
  plan_code: string;
  plan_name: string;
  status: string;
  billing_interval: "monthly" | "annual";
  stripe_customer_id?: string | null;
  stripe_subscription_id?: string | null;
  stripe_checkout_session_id?: string | null;
  current_period_start?: string | null;
  current_period_end?: string | null;
  cancel_at_period_end: boolean;
  subscribed_at: string;
  canceled_at?: string | null;
  trial_ends_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type BillingEntitlementsRead = {
  plan: BillingPlanRead;
  subscription?: BillingSubscriptionRead | null;
  features: Record<string, boolean>;
  limits: Record<string, number | null>;
  usage: Record<string, number>;
};

export type BillingCheckoutSessionResponse = {
  session_id: string;
  checkout_url: string;
  mode: "payment" | "subscription";
};

export type BillingPortalResponse = {
  portal_url: string;
};

export type AnalyticsPointRead = {
  date: string;
  value: number;
};

export type CreatorActivityItemRead = {
  event_name: string;
  created_at: string;
  payload: Record<string, unknown>;
};

export type CreatorDashboardSummaryRead = {
  published_workers_count: number;
  total_installs: number;
  total_runs: number;
  active_workers_count: number;
  paid_workers_count: number;
  free_workers_count: number;
  estimated_total_revenue: number;
  estimated_platform_share: number;
  estimated_creator_share: number;
  recent_install_trend: AnalyticsPointRead[];
  recent_run_trend: AnalyticsPointRead[];
};

export type CreatorWorkerSummaryRead = {
  worker_template_id: string;
  name: string;
  slug?: string | null;
  category: string;
  pricing_type: "free" | "subscription" | "one_time" | "internal";
  installs: number;
  runs: number;
  active_workspaces: number;
  purchase_count: number;
  estimated_revenue: number;
  moderation_status: string;
  created_at: string;
  published_at?: string | null;
};

export type CreatorWorkerAnalyticsRead = {
  worker_template_id: string;
  installs_over_time: AnalyticsPointRead[];
  runs_over_time: AnalyticsPointRead[];
  active_workspaces_over_time: AnalyticsPointRead[];
  purchases_over_time: AnalyticsPointRead[];
  revenue_over_time: AnalyticsPointRead[];
  recent_failures: Array<Record<string, unknown>>;
};

export type CreatorPayoutsSummaryRead = {
  estimated_gross_revenue: number;
  estimated_creator_share: number;
  estimated_platform_share: number;
  pending_payout_estimate: number;
  paid_out_estimate: number;
  refund_estimate: number;
  disclaimer: string;
};

export type WorkspaceAnalyticsSummaryRead = {
  installed_workers_count: number;
  published_workers_count: number;
  total_runs: number;
  runs_this_period: number;
  chain_runs_this_period: number;
  success_rate: number;
  failed_runs: number;
  top_used_workers: Array<Record<string, unknown>>;
  plan: BillingPlanRead;
  limits: Record<string, number | null>;
  usage: Record<string, number>;
  percent_of_limit_used: Record<string, number>;
};

export type WorkspaceActivityRead = {
  event_name: string;
  created_at: string;
  payload: Record<string, unknown>;
};

export type WorkspaceUsageHistoryPointRead = {
  date: string;
  worker_runs: number;
  chain_runs: number;
  installs: number;
  successful_runs: number;
  failed_runs: number;
};

export type AdminAnalyticsSummaryRead = {
  total_users: number;
  total_workspaces: number;
  total_subscriptions_active: number;
  subscriptions_by_plan: Record<string, number>;
  total_published_workers: number;
  total_marketplace_workers: number;
  total_public_workers: number;
  total_installs: number;
  total_runs: number;
  total_paid_purchases: number;
  estimated_mrr: number;
  estimated_arr_run_rate: number;
  top_workers: Array<Record<string, unknown>>;
  top_creators: Array<Record<string, unknown>>;
};

export type AdminWorkerListItemRead = {
  worker_template_id: string;
  name: string;
  slug?: string | null;
  category: string;
  pricing_type: "free" | "subscription" | "one_time" | "internal";
  visibility: "private" | "workspace" | "public" | "marketplace";
  moderation_status: string;
  report_count: number;
  is_featured: boolean;
  featured_rank: number;
  installs: number;
  runs: number;
  creator_user_id?: string | null;
};

export type OnboardingStateRead = {
  id: string;
  user_id: string;
  workspace_id: string;
  current_step: string;
  goal_category: "real_estate" | "marketing" | "sales" | "ecommerce" | "research" | "operations" | "custom" | null;
  selected_paths_json: string[];
  recommended_template_slugs: string[];
  completed_steps_json: string[];
  is_completed: boolean;
  is_skipped: boolean;
  last_completed_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type OnboardingRecommendationItem = {
  id: string;
  slug: string;
  name: string;
  short_description?: string | null;
  category: string;
  pricing_type: "free" | "subscription" | "one_time" | "internal";
  price_cents: number;
  currency: string;
  is_featured: boolean;
  featured_rank: number;
  install_count: number;
};

export type OnboardingRecommendationResponse = {
  goal_category: "real_estate" | "marketing" | "sales" | "ecommerce" | "research" | "operations" | "custom";
  templates: OnboardingRecommendationItem[];
};

export type SupportRequestRead = {
  id: string;
  workspace_id?: string | null;
  user_id?: string | null;
  handled_by_user_id?: string | null;
  name: string;
  email: string;
  subject: string;
  message: string;
  status: "open" | "in_progress" | "resolved" | "closed";
  source: string;
  resolved_at?: string | null;
  metadata_json?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type AdminWorkerDetailRead = {
  template: WorkerTemplateRead;
  creator?: {
    id: string;
    full_name: string;
    email: string;
  } | null;
  installs: number;
  runs: number;
  estimated_revenue: number;
  moderation_status: string;
  report_count: number;
  recent_reports: Array<Record<string, unknown>>;
  recent_activity: Array<Record<string, unknown>>;
};

export type AdminCreatorListItemRead = {
  creator_user_id: string;
  email: string;
  full_name: string;
  published_workers: number;
  installs: number;
  runs: number;
  estimated_revenue: number;
  moderation_issues_count: number;
  payouts_enabled: boolean;
  onboarding_complete: boolean;
};

export type AdminBillingSummaryRead = {
  active_subscriptions_by_plan: Record<string, number>;
  churned_subscriptions_count: number;
  failed_payments_count: number;
  estimated_platform_revenue: number;
  top_grossing_workers: Array<Record<string, unknown>>;
  top_grossing_creators: Array<Record<string, unknown>>;
};
