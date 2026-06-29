import { invoke } from "@tauri-apps/api/core";
import type {
  AiConfig,
  AiConfigUpdate,
  AppInfo,
  ChatRequest,
  ChatResponse,
  ChatMessage,
  Client,
  DiagnosticReport,
  EnterpriseAiDashboard,
  FeatureCheck,
  BillingConfig,
  CheckoutSession,
  CheckoutStatus,
  KnowledgeArticle,
  LicenseInfo,
  Profile,
  ProviderHealthResult,
  RepairAction,
  RepairRecord,
  RepairResult,
  ScanRecord,
  SupportCase,
  SystemScanResult,
  TechnicianNote,
  UpdateInfo,
  ReleaseDownloads,
  ConnectivityReport,
  ConnectivityDiagnosticRecord,
  UpsertAiAgentRequest,
  UpsertAiProviderRequest,
  UpdateAiOrgPolicyRequest,
  AiOrgPolicy,
  AiProviderRecord,
  AiAuditEntry,
  AgentSessionRecord,
  IntelItem,
  OrgPlaybook,
  RepairPackRecord,
  WatchdogStatus,
  WatchdogConfig,
  PsaConfig,
  PsaDeliveryResult,
} from "./types";

const isTauri = () => typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

async function invokeOrMock<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  if (isTauri()) {
    return invoke<T>(cmd, args);
  }
  const { mockInvoke } = await import("./mock");
  return mockInvoke<T>(cmd, args);
}

export const thorpeApi = {
  getAppInfo: () => invokeOrMock<AppInfo>("get_app_info"),
  checkForUpdates: () => invokeOrMock<UpdateInfo>("check_for_updates"),
  getReleaseDownloads: () => invokeOrMock<ReleaseDownloads>("get_release_downloads"),
  runConnectivityDiagnostics: (userMessage?: string, sessionId?: string) =>
    invokeOrMock<ConnectivityReport>("run_connectivity_diagnostics", {
      userMessage: userMessage ?? null,
      sessionId: sessionId ?? null,
    }),
  listConnectivityDiagnostics: (limit?: number) =>
    invokeOrMock<ConnectivityDiagnosticRecord[]>("list_connectivity_diagnostics", {
      limit: limit ?? 20,
    }),

  getProfile: () => invokeOrMock<Profile>("get_profile"),
  updateProfile: (displayName: string, email: string | null, skillLevel: string) =>
    invokeOrMock<Profile>("update_profile", { displayName, email, skillLevel }),

  getChatHistory: (limit?: number) =>
    invokeOrMock<ChatMessage[]>("get_chat_history", { limit }),

  runSystemScan: () => invokeOrMock<SystemScanResult>("run_system_scan"),
  getLastScan: () => invokeOrMock<SystemScanResult | null>("get_last_scan"),
  listScans: (limit?: number) => invokeOrMock<ScanRecord[]>("list_scans", { limit }),

  generateReport: (scanId?: string) =>
    invokeOrMock<DiagnosticReport>("generate_diagnostic_report", { scanId }),
  listReports: (limit?: number) => invokeOrMock<DiagnosticReport[]>("list_reports", { limit }),
  getReport: (id: string) => invokeOrMock<DiagnosticReport>("get_report", { id }),
  deleteReport: (id: string) => invokeOrMock<void>("delete_report", { id }),
  searchReports: (query: string) => invokeOrMock<DiagnosticReport[]>("search_reports", { query }),
  exportReportPdf: (reportId: string, outputPath: string) =>
    invokeOrMock<string>("export_report_pdf", { reportId, outputPath }),

  listRepairActions: () => invokeOrMock<RepairAction[]>("list_repair_actions"),
  executeRepair: (actionId: string, confirmed: boolean) =>
    invokeOrMock<RepairResult>("execute_repair", { actionId, confirmed }),
  listRepairHistory: (limit?: number) =>
    invokeOrMock<RepairRecord[]>("list_repair_history", { limit }),

  chatWithJonathan: (request: ChatRequest) =>
    invokeOrMock<ChatResponse>("chat_with_jonathan", { request }),
  getAiConfig: () => invokeOrMock<AiConfig>("get_ai_config"),
  setAiConfig: (config: AiConfigUpdate) => invokeOrMock<void>("set_ai_config", { config }),

  listKnowledgeArticles: (category?: string) =>
    invokeOrMock<KnowledgeArticle[]>("list_knowledge_articles", { category }),
  getKnowledgeArticle: (id: string) =>
    invokeOrMock<KnowledgeArticle>("get_knowledge_article", { id }),

  listClients: () => invokeOrMock<Client[]>("list_clients"),
  createClient: (client: Omit<Client, "id" | "created_at" | "updated_at">) =>
    invokeOrMock<Client>("create_client", { client }),
  updateClient: (id: string, client: Omit<Client, "id" | "created_at" | "updated_at">) =>
    invokeOrMock<Client>("update_client", { id, client }),

  listCases: () => invokeOrMock<SupportCase[]>("list_cases"),
  createCase: (supportCase: {
    client_id?: string;
    device_id?: string;
    title: string;
    status: string;
    priority: string;
    description?: string;
    report_id?: string;
  }) => invokeOrMock<SupportCase>("create_case", { case: supportCase }),
  updateCase: (
    id: string,
    supportCase: { title: string; status: string; priority: string; description?: string }
  ) => invokeOrMock<SupportCase>("update_case", { id, case: supportCase }),

  addTechnicianNote: (note: {
    case_id?: string;
    report_id?: string;
    author: string;
    content: string;
  }) => invokeOrMock<TechnicianNote>("add_technician_note", { note }),
  listTechnicianNotes: (caseId?: string, reportId?: string) =>
    invokeOrMock<TechnicianNote[]>("list_technician_notes", {
      caseId,
      reportId,
    }),

  getSettings: () => invokeOrMock<[string, string][]>("get_settings"),
  updateSettings: (key: string, value: string) =>
    invokeOrMock<void>("update_settings", { key, value }),
  deleteAllUserData: () => invokeOrMock<void>("delete_all_user_data"),

  getLicenseInfo: () => invokeOrMock<LicenseInfo>("get_license_info"),
  activateLicense: (licenseKey: string, organization?: string) =>
    invokeOrMock<LicenseInfo>("activate_license", {
      request: { license_key: licenseKey, organization },
    }),
  checkFeature: (feature: string) => invokeOrMock<FeatureCheck>("check_feature", { feature }),

  getBillingConfig: () => invokeOrMock<BillingConfig>("get_billing_config"),
  createBillingCheckout: (tier: string, customerEmail?: string) =>
    invokeOrMock<CheckoutSession>("create_billing_checkout", { tier, customerEmail }),
  getCheckoutStatus: (sessionId: string) =>
    invokeOrMock<CheckoutStatus>("get_checkout_status", { sessionId }),
  openExternalUrl: (url: string) => invokeOrMock<void>("open_external_url", { url }),

  getEnterpriseAiDashboard: () =>
    invokeOrMock<EnterpriseAiDashboard>("get_enterprise_ai_dashboard"),
  upsertAiProvider: (request: UpsertAiProviderRequest) =>
    invokeOrMock<AiProviderRecord>("upsert_ai_provider", { request }),
  rotateProviderApiKey: (providerId: string, apiKey: string) =>
    invokeOrMock<void>("rotate_provider_api_key", {
      request: { provider_id: providerId, api_key: apiKey },
    }),
  upsertAiAgent: (request: UpsertAiAgentRequest) =>
    invokeOrMock("upsert_ai_agent", { request }),
  updateAiOrgPolicy: (request: UpdateAiOrgPolicyRequest) =>
    invokeOrMock<AiOrgPolicy>("update_ai_org_policy", { request }),
  testAiProviderHealth: (providerId: string) =>
    invokeOrMock<ProviderHealthResult>("test_ai_provider_health", { providerId }),
  listAiAuditLog: (limit?: number) =>
    invokeOrMock<AiAuditEntry[]>("list_ai_audit_log", { limit }),

  listAgentSessions: (limit?: number) =>
    invokeOrMock<AgentSessionRecord[]>("list_agent_sessions", { limit }),
  syncIntelFeed: () => invokeOrMock<number>("sync_intel_feed"),
  listIntelItems: (limit?: number) =>
    invokeOrMock<IntelItem[]>("list_intel_items", { limit }),
  listRepairPacks: () => invokeOrMock<RepairPackRecord[]>("list_repair_packs"),
  installRepairPack: (manifestJson: string) =>
    invokeOrMock<RepairPackRecord>("install_repair_pack", { manifestJson }),
  upsertOrgPlaybook: (title: string, category: string, content: string, tags: string[]) =>
    invokeOrMock<OrgPlaybook>("upsert_org_playbook", { title, category, content, tags }),
  listOrgPlaybooks: () => invokeOrMock<OrgPlaybook[]>("list_org_playbooks"),
  getWatchdogStatus: () => invokeOrMock<WatchdogStatus>("get_watchdog_status"),
  updateWatchdogConfig: (
    enabled: boolean,
    intervalMinutes: number,
    healthThreshold: number,
    autoNotify: boolean,
    autoPlan: boolean
  ) =>
    invokeOrMock<WatchdogConfig>("update_watchdog_config", {
      enabled,
      intervalMinutes,
      healthThreshold,
      autoNotify,
      autoPlan,
    }),
  acknowledgeWatchdogEvent: (eventId: string) =>
    invokeOrMock<void>("acknowledge_watchdog_event", { eventId }),
  getPsaSettings: () => invokeOrMock<PsaConfig>("get_psa_settings"),
  updatePsaSettings: (
    enabled: boolean,
    webhookUrl: string | null,
    provider: string,
    secret?: string
  ) =>
    invokeOrMock<PsaConfig>("update_psa_settings", {
      enabled,
      webhookUrl,
      provider,
      secret,
    }),
  testPsaWebhook: (webhookUrl?: string, secret?: string) =>
    invokeOrMock<PsaDeliveryResult>("test_psa_webhook", {
      webhookUrl,
      secret,
    }),
  exportAgentSessionPdf: (sessionId: string, outputPath: string) =>
    invokeOrMock<string>("export_agent_session_pdf", { sessionId, outputPath }),
};
