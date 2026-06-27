import { invoke } from "@tauri-apps/api/core";
import type {
  AiConfig,
  AppInfo,
  ChatRequest,
  ChatResponse,
  Client,
  DiagnosticReport,
  FeatureCheck,
  KnowledgeArticle,
  LicenseInfo,
  Profile,
  RepairAction,
  RepairRecord,
  RepairResult,
  ScanRecord,
  SupportCase,
  SystemScanResult,
  TechnicianNote,
  UpdateInfo,
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

  getProfile: () => invokeOrMock<Profile>("get_profile"),
  updateProfile: (displayName: string, email: string | null, skillLevel: string) =>
    invokeOrMock<Profile>("update_profile", { displayName, email, skillLevel }),

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
  setAiConfig: (config: AiConfig) => invokeOrMock<void>("set_ai_config", { config }),

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
};
