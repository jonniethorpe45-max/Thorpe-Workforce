import type { KnowledgeArticle, LicenseInfo, SystemScanResult } from "./types";
import { extractFirstName } from "../lib/userName";

type MockLicenseState = {
  tier: string;
  license_key: string | null;
  activated_at: string | null;
  expires_at: string | null;
  organization: string | null;
};

const mockLicense: MockLicenseState = {
  tier: "free",
  license_key: null,
  activated_at: null,
  expires_at: null,
  organization: null,
};

function mockTierFeatures(tier: string): string[] {
  if (tier === "enterprise") {
    return [
      "jonathan_ai",
      "basic_scans",
      "full_diagnostics",
      "repair_center",
      "pdf_export",
      "unlimited_reports",
      "technician_workspace",
      "enterprise_ai_console",
      "intelligence_console",
    ];
  }
  if (tier === "professional") {
    return [
      "jonathan_ai",
      "basic_scans",
      "full_diagnostics",
      "repair_center",
      "pdf_export",
      "unlimited_reports",
    ];
  }
  return ["jonathan_ai", "jonathan_auto_repair", "basic_scans", "limited_reports"];
}

function mockTierDisplay(tier: string): string {
  if (tier === "enterprise") return "Enterprise";
  if (tier === "professional") return "Professional";
  return "Free";
}

function mockFeatureRequiredTier(feature: string): string {
  if (["jonathan_ai", "jonathan_auto_repair", "basic_scans", "limited_reports"].includes(feature)) {
    return "free";
  }
  if (["full_diagnostics", "repair_center", "pdf_export", "unlimited_reports"].includes(feature)) {
    return "professional";
  }
  return "enterprise";
}

function mockTierLevel(tier: string): number {
  if (tier === "enterprise") return 3;
  if (tier === "professional") return 2;
  return 1;
}

function mockLicenseInfo(): LicenseInfo {
  return {
    tier: mockLicense.tier,
    tier_display: mockTierDisplay(mockLicense.tier),
    features: mockTierFeatures(mockLicense.tier),
    license_key: mockLicense.license_key,
    activated_at: mockLicense.activated_at,
    expires_at: mockLicense.expires_at,
    organization: mockLicense.organization,
  };
}

function mockHasFeature(feature: string): boolean {
  const features = mockTierFeatures(mockLicense.tier);
  const required = mockFeatureRequiredTier(feature);
  return features.includes(feature) || mockTierLevel(mockLicense.tier) >= mockTierLevel(required);
}

function requireMockFeature(feature: string): void {
  if (!mockHasFeature(feature)) {
    const required = mockFeatureRequiredTier(feature);
    throw new Error(
      `This feature requires a ${mockTierDisplay(required)} license. Upgrade in Licensing settings.`
    );
  }
}

export function resetMockState(): void {
  mockLicense.tier = "free";
  mockLicense.license_key = null;
  mockLicense.activated_at = null;
  mockLicense.expires_at = null;
  mockLicense.organization = null;
}

const mockScan: SystemScanResult = {
  id: "mock-scan-1",
  timestamp: new Date().toISOString(),
  health_score: 82,
  os: {
    name: "Linux",
    version: "6.1.0",
    hostname: "dev-machine",
    kernel_version: "6.1.0",
    arch: "x86_64",
  },
  cpu: { brand: "Intel Core i7", cores: 8, usage_percent: 23.5 },
  memory: { total_gb: 16, used_gb: 8.2, available_gb: 7.8, usage_percent: 51.3 },
  disks: [
    {
      name: "/dev/sda1",
      mount_point: "/",
      total_gb: 256,
      used_gb: 180,
      available_gb: 76,
      usage_percent: 70.3,
      file_system: "ext4",
    },
  ],
  battery: null,
  network: {
    interfaces: [{ name: "eth0", received_mb: 1024, transmitted_mb: 512 }],
    total_received_mb: 1024,
    total_transmitted_mb: 512,
  },
  processes: [
    { pid: 1234, name: "chrome", cpu_usage: 12.5, memory_mb: 512 },
    { pid: 5678, name: "code", cpu_usage: 8.2, memory_mb: 1024 },
  ],
  startup_apps: ["Review startup items in system settings"],
  installed_software: ["Platform: linux"],
  hardware_summary: {
    cpu_brand: "Intel Core i7",
    total_memory_gb: 16,
    total_disk_gb: 256,
    disk_count: 1,
  },
  issues: [
    {
      id: "disk-usage",
      title: "Moderate disk usage",
      description: "Root partition is 70% full.",
      severity: "low",
      category: "storage",
    },
  ],
  updates_available: false,
};

const mockArticles: KnowledgeArticle[] = [
  {
    id: "kb-windows-slow-boot",
    category: "Windows",
    title: "Slow Windows Startup",
    symptoms: "Computer takes several minutes to boot.",
    causes: "Too many startup programs.",
    fixes: "Disable unnecessary startup programs in Task Manager.",
    prevention: "Keep startup programs minimal.",
    when_to_escalate: "If boot time exceeds 5 minutes after optimization.",
    tags: '["performance"]',
    created_at: new Date().toISOString(),
  },
  {
    id: "kb-network-dns",
    category: "Networking",
    title: "DNS Resolution Failures",
    symptoms: "Websites won't load but ping works.",
    causes: "Incorrect DNS settings.",
    fixes: "Flush DNS cache and switch to public DNS.",
    prevention: "Use reliable DNS providers.",
    when_to_escalate: "If DNS fails on all devices.",
    tags: '["networking"]',
    created_at: new Date().toISOString(),
  },
];

export async function mockInvoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  await new Promise((r) => setTimeout(r, 300));

  switch (cmd) {
    case "get_app_info":
      return {
        name: "Thorpe",
        version: "1.1.0",
        platform: "linux",
        data_dir: "/tmp/thorpe",
      } as T;

    case "get_profile":
      return {
        id: "mock-profile",
        display_name: "Alex Johnson",
        email: null,
        skill_level: "beginner",
        role: "admin",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      } as T;

    case "run_system_scan":
    case "get_last_scan":
      return { ...mockScan, id: `mock-${Date.now()}` } as T;

    case "list_scans":
      return [
        {
          id: mockScan.id,
          scan_data: JSON.stringify(mockScan),
          health_score: mockScan.health_score,
          created_at: mockScan.timestamp,
        },
      ] as T;

    case "generate_diagnostic_report":
      return {
        id: `report-${Date.now()}`,
        scan_id: mockScan.id,
        title: "System Diagnostic Report",
        summary: `Health score: ${mockScan.health_score}/100`,
        findings: JSON.stringify(mockScan.issues),
        recommendations: JSON.stringify([{ action: "Run disk cleanup" }]),
        health_score: mockScan.health_score,
        risk_level: "low",
        technician_notes: null,
        plain_language: "Your system is in good shape overall.",
        created_at: new Date().toISOString(),
      } as T;

    case "list_reports":
      return [] as T;

    case "get_report":
      return {
        id: (args?.id as string) || "report-1",
        scan_id: mockScan.id,
        title: "System Diagnostic Report",
        summary: `Health score: ${mockScan.health_score}/100`,
        findings: JSON.stringify(mockScan.issues),
        recommendations: "[]",
        health_score: mockScan.health_score,
        risk_level: "low",
        technician_notes: null,
        plain_language: "Your system is in good shape overall.",
        created_at: new Date().toISOString(),
      } as T;

    case "search_reports":
      return [] as T;

    case "delete_report":
    case "delete_all_user_data":
    case "set_ai_config":
    case "update_settings":
    case "open_external_url":
    case "rotate_provider_api_key":
      return undefined as T;

    case "update_profile":
      return {
        id: "mock-profile",
        display_name: (args?.displayName as string) || "Alex Johnson",
        email: (args?.email as string | null) ?? null,
        skill_level: (args?.skillLevel as string) || "beginner",
        role: "admin",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      } as T;

    case "export_report_pdf":
      return ((args?.outputPath as string) || "/tmp/report.pdf") as T;

    case "create_client": {
      requireMockFeature("technician_workspace");
      const client = args?.client as Record<string, string> | undefined;
      return {
        id: `client-${Date.now()}`,
        name: client?.name ?? "Acme Corp",
        email: client?.email ?? "support@acme.test",
        phone: null,
        company: client?.company ?? "Acme",
        notes: client?.notes ?? null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      } as T;
    }

    case "update_client":
      requireMockFeature("technician_workspace");
      return {
        id: (args?.id as string) || "client-1",
        name: "Acme Corp",
        email: "support@acme.test",
        phone: null,
        company: "Acme",
        notes: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      } as T;

    case "create_case": {
      requireMockFeature("technician_workspace");
      const supportCase = args?.case as Record<string, string> | undefined;
      return {
        id: `case-${Date.now()}`,
        client_id: supportCase?.client_id ?? null,
        title: supportCase?.title ?? "New case",
        description: supportCase?.description ?? "",
        status: "open",
        priority: supportCase?.priority ?? "medium",
        assigned_to: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      } as T;
    }

    case "update_case":
      requireMockFeature("technician_workspace");
      return {
        id: (args?.id as string) || "case-1",
        client_id: null,
        title: "Updated case",
        description: "",
        status: "open",
        priority: "medium",
        assigned_to: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      } as T;

    case "add_technician_note":
      requireMockFeature("technician_workspace");
      return {
        id: `note-${Date.now()}`,
        case_id: null,
        report_id: null,
        author: "Alex Johnson",
        content: "Test note",
        created_at: new Date().toISOString(),
      } as T;

    case "list_repair_actions":
      return [
        {
          id: "temp-cleanup",
          name: "Clean Temporary Files",
          description: "Remove temporary files.",
          purpose: "Free disk space.",
          risk_level: "low",
          category: "storage",
          requires_confirmation: true,
          action_kind: "mutating",
          platform: ["linux"],
        },
        {
          id: "dns-flush",
          name: "Flush DNS Cache",
          description: "Clear DNS cache.",
          purpose: "Fix DNS issues.",
          risk_level: "low",
          category: "network",
          requires_confirmation: true,
          action_kind: "mutating",
          platform: ["linux"],
        },
      ] as T;

    case "execute_repair":
      return {
        success: true,
        message: "Repair completed (mock mode).",
        details: "This is a browser preview — run in Tauri for real repairs.",
        record_id: `repair-${Date.now()}`,
      } as T;

    case "list_repair_history":
      return [] as T;

    case "chat_with_jonathan": {
      const req = args?.request as {
        message: string;
        confirmed_repairs?: string[];
      };
      const msg = req?.message?.toLowerCase() || "";
      const confirmed = new Set(req?.confirmed_repairs ?? []);
      const firstName = extractFirstName("Alex Johnson");
      const isNetwork = msg.includes("wifi") || msg.includes("network") || msg.includes("internet");
      const connectivityReport = isNetwork
        ? {
            checks: [
              { name: "Network adapter", status: "pass", detail: "Active interface: wlan0" },
              { name: "Default gateway", status: "pass", detail: "Reachable: 192.168.1.1" },
              { name: "DNS resolution", status: "fail", detail: "Could not resolve example.com" },
              { name: "Internet (1.1.1.1)", status: "pass", detail: "Reachable: 1.1.1.1" },
            ],
            overall_status: "degraded",
            recommended_actions: ["dns-flush", "connectivity-suite"],
            playbook_summary:
              "Internet reachability looks OK but DNS resolution failed. Flushing the DNS cache is the next step.",
            offline_capable: true,
          }
        : null;
      const repairs = [];
      if (isNetwork) {
        repairs.push({
          success: true,
          message: "Offline connectivity diagnostics complete.",
          details:
            "Overall status: degraded\n\nChecks:\n  ✓ Network adapter — Active interface: wlan0\n  ✗ DNS resolution — Could not resolve example.com",
          record_id: "mock-repair-1",
          action_id: "connectivity-suite",
          action_name: "Offline Connectivity Suite",
          action_kind: "diagnostic",
        });
        if (confirmed.has("dns-flush")) {
          repairs.push({
            success: true,
            message: "DNS cache flushed successfully.",
            details: null,
            record_id: "mock-repair-2",
            action_id: "dns-flush",
            action_name: "Flush DNS Cache",
            action_kind: "mutating",
          });
        }
      } else if (msg.includes("slow") && confirmed.has("temp-cleanup")) {
        repairs.push({
          success: true,
          message: "Temporary files cleaned (mock mode).",
          details: null,
          record_id: "mock-repair-3",
          action_id: "temp-cleanup",
          action_name: "Clean Temporary Files",
          action_kind: "mutating",
        });
      }
      const pending_repairs = [];
      if (isNetwork && !confirmed.has("dns-flush")) {
        pending_repairs.push({
          id: "dns-flush",
          name: "Flush DNS Cache",
          description: "Clear DNS cache.",
          purpose: "Fix DNS issues.",
          risk_level: "low",
          category: "network",
          requires_confirmation: true,
          action_kind: "mutating",
          platform: ["linux"],
        });
      }
      if (msg.includes("slow") && !confirmed.has("temp-cleanup")) {
        pending_repairs.push({
          id: "temp-cleanup",
          name: "Clean Temporary Files",
          description: "Remove temporary files",
          purpose: "Free disk space",
          risk_level: "low",
          category: "storage",
          requires_confirmation: true,
          action_kind: "mutating",
          platform: ["linux"],
        });
      }
      const greeting = firstName ? `**Hi ${firstName}, here's what I did**` : "**Jonathan — here's what I did**";
      const closing = firstName
        ? `Let me know if you need anything else, ${firstName}.`
        : "Let me know if you need anything else.";
      let response =
        repairs.length > 0
          ? `${greeting}\n\n**Diagnostics run:**\n- ✓ **Offline Connectivity Suite** — Offline connectivity diagnostics complete.\n\n`
          : `${greeting}\n\nI analyzed your request but no automated actions were run.\n\n`;
      if (repairs.some((r) => r.action_id === "dns-flush")) {
        response += "**Repairs applied:**\n- ✓ **Flush DNS Cache** — DNS cache flushed successfully.\n\n";
      }
      if (repairs.some((r) => r.action_id === "temp-cleanup")) {
        response += "**Repairs applied:**\n- ✓ **Clean Temporary Files** — Temporary files cleaned.\n\n";
      }
      if (connectivityReport) {
        response += `**Offline connectivity check** (runs locally — no internet required):\n- Overall: **degraded**\n- ${connectivityReport.playbook_summary}\n`;
      }
      response += closing;
      return {
        message: response,
        source: "local",
        repairs_executed: repairs,
        pending_repairs,
        verification: repairs.some((r) => r.action_kind === "mutating")
          ? {
              health_before: 78,
              health_after: 82,
              issues_before: 2,
              issues_after: 1,
              improved: true,
            }
          : null,
        escalation_case_id: msg.includes("virus") ? "mock-case-1" : null,
        kb_suggestions: isNetwork
          ? [
              {
                id: "kb-network-dns",
                title: "DNS Resolution Failures",
                summary: "Websites won't load but ping works.",
                source: "knowledge_base",
              },
            ]
          : [],
        connectivity_report: connectivityReport,
      } as T;
    }

    case "run_connectivity_diagnostics":
      return {
        checks: [
          { name: "Network adapter", status: "pass", detail: "Active interface: wlan0" },
          { name: "Internet (1.1.1.1)", status: "pass", detail: "Reachable: 1.1.1.1" },
        ],
        overall_status: "healthy",
        recommended_actions: ["connectivity-suite"],
        playbook_summary: "Core connectivity checks passed.",
        offline_capable: true,
      } as T;

    case "list_connectivity_diagnostics":
      return [] as T;

    case "get_chat_history":
      return [] as T;

    case "get_ai_config":
      return {
        provider: "openai",
        api_key_configured: false,
        model: "gpt-4o-mini",
        base_url: "https://api.openai.com/v1",
        enabled: false,
      } as T;

    case "list_knowledge_articles":
      return mockArticles as T;

    case "get_knowledge_article": {
      const id = args?.id as string;
      return (mockArticles.find((a) => a.id === id) || mockArticles[0]) as T;
    }

    case "get_license_info":
      return mockLicenseInfo() as T;

    case "activate_license": {
      const key = ((args?.request as { license_key?: string })?.license_key ?? "").toUpperCase();
      const tier = key.startsWith("ENT-") ? "enterprise" : key.startsWith("PRO-") ? "professional" : "free";
      mockLicense.tier = tier;
      mockLicense.license_key = key || null;
      mockLicense.activated_at = tier === "free" ? null : new Date().toISOString();
      mockLicense.expires_at = null;
      mockLicense.organization = null;
      return mockLicenseInfo() as T;
    }

    case "get_billing_config":
      return {
        billing_api_url: null,
        stripe_configured: false,
        license_api_url: null,
      } as T;

    case "create_billing_checkout": {
      const tier = (args?.tier as string) ?? "professional";
      return {
        session_id: "mock-checkout-session",
        checkout_url: `https://checkout.stripe.com/mock/${tier}`,
        stripe_configured: true,
      } as T;
    }

    case "get_checkout_status": {
      const sessionId = (args?.sessionId as string) ?? "mock-checkout-session";
      return {
        session_id: sessionId,
        status: "complete",
        tier: "professional",
        license_key: "PRO-MOCK-0001-PAID-B65C",
      } as T;
    }

    case "check_feature": {
      const feature = args?.feature as string;
      const allowed = mockHasFeature(feature);
      return {
        feature,
        allowed,
        required_tier: mockFeatureRequiredTier(feature),
      } as T;
    }

    case "get_enterprise_ai_dashboard":
      return {
        providers: [
          {
            id: "openai-default",
            name: "OpenAI",
            provider_type: "openai",
            base_url: "https://api.openai.com/v1",
            enabled: true,
            api_key_configured: false,
            health_status: "unknown",
            health_message: null,
            last_health_check_at: null,
            allowed_roles: ["admin", "technician", "user"],
          },
          {
            id: "anthropic-default",
            name: "Anthropic",
            provider_type: "anthropic",
            base_url: "https://api.anthropic.com/v1",
            enabled: true,
            api_key_configured: false,
            health_status: "unknown",
            health_message: null,
            last_health_check_at: null,
            allowed_roles: ["admin", "technician"],
          },
        ],
        agents: [
          {
            id: "agent-jonathan",
            agent_key: "jonathan",
            name: "Jonathan",
            provider_id: "openai-default",
            model: "gpt-4o-mini",
            enabled: true,
            allowed_roles: ["admin", "technician", "user"],
          },
        ],
        policy: {
          cloud_ai_enabled: true,
          default_provider_id: "openai-default",
          monthly_budget_usd: 100,
          monthly_token_limit: 1000000,
          enforce_budget: true,
          updated_at: new Date().toISOString(),
        },
        usage: {
          month: new Date().toISOString().slice(0, 7),
          total_tokens: 12500,
          prompt_tokens: 8000,
          completion_tokens: 4500,
          estimated_cost_usd: 2.45,
          request_count: 42,
          budget_used_percent: 2.45,
          token_limit_used_percent: 1.25,
        },
        audit_log: [
          {
            id: "audit-1",
            action: "provider.created",
            actor: "Alex Johnson",
            details: "Created provider OpenAI",
            created_at: new Date().toISOString(),
          },
        ],
        roles: ["admin", "technician", "user"],
      } as T;

    case "upsert_ai_provider":
    case "upsert_ai_agent":
    case "update_ai_org_policy":
    case "test_ai_provider_health":
      return {} as T;

    case "list_ai_audit_log":
      return [] as T;

    case "check_for_updates":
      return {
        current_version: "1.1.0",
        latest_version: "1.0.8",
        update_available: false,
        release_notes: "You are running the latest version.",
        download_url:
          "https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/download/v1.0.8/Thorpe_1.0.8_x64-setup.exe",
        check_error: null,
      } as T;

    case "get_release_downloads":
      return {
        release_version: "1.0.8",
        releases_page: "https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/latest",
        windows_exe:
          "https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/download/v1.0.8/Thorpe_1.0.8_x64-setup.exe",
        windows_msi:
          "https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/download/v1.0.8/Thorpe_1.0.8_x64_en-US.msi",
        macos_dmg:
          "https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/download/v1.0.8/Thorpe_1.0.8_aarch64.dmg",
        linux_appimage:
          "https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/download/v1.0.8/Thorpe_1.0.8_amd64.AppImage",
        linux_deb:
          "https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/download/v1.0.8/Thorpe_1.0.8_amd64.deb",
      } as T;

    case "list_intel_items":
      return [
        {
          id: "intel-1",
          source: "thorpe-feed",
          category: "Windows",
          title: "Print spooler instability after KB update",
          summary: "Restart Print Spooler service if jobs stall after recent Windows updates.",
          url: "https://support.microsoft.com",
          severity: "medium",
          published_at: new Date().toISOString(),
          fetched_at: new Date().toISOString(),
        },
      ] as T;

    case "sync_intel_feed":
      return 1 as T;

    case "list_org_playbooks":
      return [] as T;

    case "upsert_org_playbook":
      return {
        id: "pb-mock",
        title: (args?.title as string) || "Playbook",
        category: (args?.category as string) || "General",
        content: (args?.content as string) || "",
        tags: "[]",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      } as T;

    case "list_repair_packs":
      return [
        {
          id: "pack-core",
          name: "Thorpe Core Repairs",
          version: "1.0.0",
          description: "Built-in diagnostic and cleanup tools.",
          enabled: true,
          builtin: true,
          manifest_json: "{}",
          installed_at: new Date().toISOString(),
        },
      ] as T;

    case "install_repair_pack":
      return {
        id: "pack-custom",
        name: "Custom Pack",
        version: "1.0.0",
        description: "Installed from manifest.",
        enabled: true,
        builtin: false,
        manifest_json: (args?.manifestJson as string) || "{}",
        installed_at: new Date().toISOString(),
      } as T;

    case "list_agent_sessions":
      return [] as T;

    case "get_watchdog_status":
      return {
        config: {
          enabled: false,
          interval_minutes: 30,
          health_threshold: 70,
          auto_notify: true,
          auto_plan: true,
          updated_at: new Date().toISOString(),
        },
        recent_events: [],
      } as T;

    case "update_watchdog_config":
      return {
        enabled: args?.enabled as boolean,
        interval_minutes: args?.intervalMinutes as number,
        health_threshold: args?.healthThreshold as number,
        auto_notify: args?.autoNotify as boolean,
        auto_plan: args?.autoPlan as boolean,
        updated_at: new Date().toISOString(),
      } as T;

    case "acknowledge_watchdog_event":
      return undefined as T;

    case "get_psa_settings":
      return {
        enabled: false,
        webhook_url: null,
        provider: "generic",
      } as T;

    case "update_psa_settings":
      return {
        enabled: args?.enabled as boolean,
        webhook_url: (args?.webhookUrl as string) || null,
        provider: (args?.provider as string) || "generic",
      } as T;

    case "test_psa_webhook":
      return {
        success: true,
        status_code: 200,
        message: args?.webhookUrl
          ? `Mock PSA webhook delivered to ${args.webhookUrl}.`
          : "Mock PSA webhook delivered.",
      } as T;

    case "export_agent_session_pdf":
      return ((args?.outputPath as string) || "/tmp/agent-session.pdf") as T;

    case "list_clients":
    case "list_cases":
    case "list_technician_notes":
      requireMockFeature("technician_workspace");
      return [] as T;

    case "get_settings":
      return [] as T;

    default:
      console.warn(`Mock: unhandled command ${cmd}`);
      return {} as T;
  }
}
