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
  platform: string[];
}

export interface RepairResult {
  success: boolean;
  message: string;
  details: string | null;
  record_id: string;
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

export interface AiConfig {
  provider: string;
  api_key: string | null;
  model: string;
  base_url: string;
  enabled: boolean;
}

export interface ChatRequest {
  message: string;
  skill_level: string;
  scan_context?: string;
  history: Array<{ role: string; content: string }>;
}

export interface ChatResponse {
  message: string;
  source: string;
}

export interface UpdateInfo {
  current_version: string;
  latest_version: string;
  update_available: boolean;
  release_notes: string;
  download_url: string;
}
