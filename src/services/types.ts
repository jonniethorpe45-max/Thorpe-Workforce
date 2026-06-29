export type LicenseTier = "free" | "professional" | "enterprise";

export interface AppInfo {
  name: string;
  version: string;
  platform: string;
  data_dir: string;
}

export interface Profile {
  id: string;
  display_name: string;
  email: string | null;
  skill_level: string;
  role: string;
  created_at: string;
  updated_at: string;
}

export interface ScanIssue {
  id: string;
  title: string;
  description: string;
  severity: string;
  category: string;
}

export interface SystemScanResult {
  id: string;
  timestamp: string;
  health_score: number;
  os: { name: string; version: string; hostname: string; kernel_version: string; arch: string };
  cpu: { brand: string; cores: number; usage_percent: number };
  memory: { total_gb: number; used_gb: number; available_gb: number; usage_percent: number };
  disks: Array<{
    name: string;
    mount_point: string;
    total_gb: number;
    used_gb: number;
    available_gb: number;
    usage_percent: number;
    file_system: string;
  }>;
  battery: { percentage: number; charging: boolean; time_remaining_minutes?: number } | null;
  network: {
    interfaces: Array<{ name: string; received_mb: number; transmitted_mb: number }>;
    total_received_mb: number;
    total_transmitted_mb: number;
  };
  processes: Array<{ pid: number; name: string; cpu_usage: number; memory_mb: number }>;
  startup_apps: string[];
  installed_software: string[];
  hardware_summary: {
    cpu_brand: string;
    total_memory_gb: number;
    total_disk_gb: number;
    disk_count: number;
  };
  issues: ScanIssue[];
  updates_available: boolean;
}

export interface ScanRecord {
  id: string;
  scan_data: string;
  health_score: number;
  created_at: string;
}

export interface DiagnosticReport {
  id: string;
  scan_id: string | null;
  title: string;
  summary: string;
  findings: string;
  recommendations: string;
  health_score: number;
  risk_level: string;
  technician_notes: string | null;
  plain_language: string;
  created_at: string;
}

export interface RepairAction {
  id: string;
  name: string;
  description: string;
  purpose: string;
  risk_level: string;
  category: string;
  requires_confirmation: boolean;
  action_kind: string;
  platform: string[];
}

export interface RepairResult {
  success: boolean;
  message: string;
  details: string | null;
  record_id: string;
  action_id?: string;
  action_name?: string;
  action_kind?: string;
}

export interface RepairRecord {
  id: string;
  action_id: string;
  action_name: string;
  status: string;
  details: string | null;
  risk_level: string;
  created_at: string;
}

export interface KnowledgeArticle {
  id: string;
  category: string;
  title: string;
  symptoms: string;
  causes: string;
  fixes: string;
  prevention: string;
  when_to_escalate: string;
  tags: string;
  created_at: string;
}

export interface Client {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  company: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface SupportCase {
  id: string;
  client_id: string | null;
  device_id: string | null;
  title: string;
  status: string;
  priority: string;
  description: string | null;
  report_id: string | null;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
}

export interface TechnicianNote {
  id: string;
  case_id: string | null;
  report_id: string | null;
  author: string;
  content: string;
  created_at: string;
}

export interface LicenseInfo {
  tier: string;
  tier_display: string;
  features: string[];
  license_key: string | null;
  activated_at: string | null;
  expires_at: string | null;
  organization: string | null;
}

export interface FeatureCheck {
  feature: string;
  allowed: boolean;
  required_tier: string;
}

export interface BillingConfig {
  billing_api_url: string | null;
  stripe_configured: boolean;
  license_api_url: string | null;
}

export interface CheckoutSession {
  session_id: string;
  checkout_url: string;
  stripe_configured: boolean;
}

export interface CheckoutStatus {
  session_id: string;
  status: string;
  tier: string | null;
  license_key: string | null;
}

export interface AiConfig {
  provider: string;
  api_key_configured: boolean;
  model: string;
  base_url: string;
  enabled: boolean;
}

export interface AiConfigUpdate {
  provider: string;
  api_key?: string | null;
  model: string;
  base_url: string;
  enabled: boolean;
}

export interface ChatRequest {
  message: string;
  skill_level: string;
  scan_context?: string;
  history: Array<{ role: string; content: string }>;
  confirmed_repairs?: string[];
}

export interface RepairVerification {
  health_before: number;
  health_after: number;
  issues_before: number;
  issues_after: number;
  improved: boolean;
}

export interface KbSuggestion {
  id: string;
  title: string;
  summary: string;
  source?: string;
}

export interface AgentPlanStep {
  tool_id: string;
  reason: string;
  risk: string;
  requires_approval: boolean;
}

export interface AgentPlan {
  hypotheses: string[];
  confidence: number;
  steps: AgentPlanStep[];
  citations: string[];
  escalate_if: string[];
}

export interface ChatResponse {
  message: string;
  source: string;
  repairs_executed?: RepairResult[];
  pending_repairs?: RepairAction[];
  verification?: RepairVerification | null;
  escalation_case_id?: string | null;
  kb_suggestions?: KbSuggestion[];
  agent_plan?: AgentPlan | null;
  agent_session_id?: string | null;
  connectivity_report?: ConnectivityReport | null;
}

export interface ChatMessage {
  id: string;
  role: string;
  content: string;
  metadata_json?: string | null;
  created_at: string;
}

export interface AssistantChatMetadata {
  source?: string;
  repairs_executed?: RepairResult[];
  pending_repairs?: RepairAction[];
  verification?: RepairVerification | null;
  escalation_case_id?: string | null;
  kb_suggestions?: KbSuggestion[];
  agent_plan?: AgentPlan | null;
  agent_session_id?: string | null;
  connectivity_report?: ConnectivityReport | null;
}

export interface ConnectivityCheck {
  name: string;
  status: string;
  detail: string;
}

export interface ConnectivityReport {
  checks: ConnectivityCheck[];
  overall_status: string;
  recommended_actions: string[];
  playbook_summary: string;
  offline_capable: boolean;
}

export interface ConnectivityDiagnosticRecord {
  id: string;
  session_id: string | null;
  user_message: string | null;
  overall_status: string;
  playbook_summary: string;
  results_json: string;
  recommended_actions_json: string;
  created_at: string;
}

export interface UpdateInfo {
  current_version: string;
  latest_version: string;
  update_available: boolean;
  release_notes: string;
  download_url: string;
  check_error?: string | null;
}

export interface ReleaseDownloads {
  release_version: string;
  releases_page: string;
  windows_exe: string | null;
  windows_msi: string | null;
  macos_dmg: string | null;
  linux_appimage: string | null;
  linux_deb: string | null;
}

export interface AiProviderRecord {
  id: string;
  name: string;
  provider_type: string;
  base_url: string;
  enabled: boolean;
  api_key_configured: boolean;
  health_status: string;
  health_message: string | null;
  last_health_check_at: string | null;
  allowed_roles: string[];
}

export interface AiAgentRecord {
  id: string;
  agent_key: string;
  name: string;
  provider_id: string | null;
  model: string;
  enabled: boolean;
  allowed_roles: string[];
}

export interface AiOrgPolicy {
  cloud_ai_enabled: boolean;
  default_provider_id: string | null;
  monthly_budget_usd: number;
  monthly_token_limit: number;
  enforce_budget: boolean;
  updated_at: string;
}

export interface AiUsageSummary {
  month: string;
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  estimated_cost_usd: number;
  request_count: number;
  budget_used_percent: number;
  token_limit_used_percent: number;
}

export interface AiAuditEntry {
  id: string;
  action: string;
  actor: string;
  details: string;
  created_at: string;
}

export interface EnterpriseAiDashboard {
  providers: AiProviderRecord[];
  agents: AiAgentRecord[];
  policy: AiOrgPolicy;
  usage: AiUsageSummary;
  audit_log: AiAuditEntry[];
  roles: string[];
}

export interface UpsertAiProviderRequest {
  id?: string;
  name: string;
  provider_type: string;
  base_url: string;
  enabled: boolean;
  api_key?: string;
  allowed_roles: string[];
}

export interface UpsertAiAgentRequest {
  agent_key: string;
  name: string;
  provider_id: string | null;
  model: string;
  enabled: boolean;
  allowed_roles: string[];
}

export interface UpdateAiOrgPolicyRequest {
  cloud_ai_enabled: boolean;
  default_provider_id: string | null;
  monthly_budget_usd: number;
  monthly_token_limit: number;
  enforce_budget: boolean;
}

export interface ProviderHealthResult {
  provider_id: string;
  status: string;
  message: string;
  checked_at: string;
}

export interface IntelItem {
  id: string;
  source: string;
  category: string;
  title: string;
  summary: string;
  url: string | null;
  severity: string;
  published_at: string;
  fetched_at: string;
}

export interface OrgPlaybook {
  id: string;
  title: string;
  category: string;
  content: string;
  tags: string;
  created_at: string;
  updated_at: string;
}

export interface RepairPackRecord {
  id: string;
  name: string;
  version: string;
  description: string;
  enabled: boolean;
  builtin: boolean;
  manifest_json: string;
  installed_at: string;
}

export interface AgentSessionRecord {
  id: string;
  case_id: string | null;
  message: string;
  plan_json: string;
  evidence_json: string | null;
  status: string;
  confidence: number;
  created_at: string;
}

export interface WatchdogConfig {
  enabled: boolean;
  interval_minutes: number;
  health_threshold: number;
  auto_notify: boolean;
  auto_plan: boolean;
  updated_at: string;
}

export interface WatchdogEvent {
  id: string;
  event_type: string;
  health_score: number;
  message: string;
  plan_json: string | null;
  acknowledged: boolean;
  created_at: string;
}

export interface WatchdogStatus {
  config: WatchdogConfig;
  recent_events: WatchdogEvent[];
}

export interface PsaConfig {
  enabled: boolean;
  webhook_url: string | null;
  provider: string;
}

export interface PsaDeliveryResult {
  success: boolean;
  status_code: number | null;
  message: string;
}
