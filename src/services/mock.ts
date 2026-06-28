import type { KnowledgeArticle, SystemScanResult } from "./types";
import { extractFirstName } from "../lib/userName";

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
      const req = args?.request as { message: string };
      const msg = req?.message?.toLowerCase() || "";
      const firstName = extractFirstName("Alex Johnson");
      const repairs =
        msg.includes("wifi") || msg.includes("network")
          ? [
              {
                success: true,
                message: "DNS cache flushed successfully.",
                details: null,
                record_id: "mock-repair-1",
                action_id: "dns-flush",
                action_name: "Flush DNS Cache",
                action_kind: "mutating",
              },
            ]
          : [];
      const greeting = firstName ? `**Hi ${firstName}, here's what I did**` : "**Jonathan — here's what I did**";
      const closing = firstName
        ? `Let me know if you need anything else, ${firstName}.`
        : "Let me know if you need anything else.";
      const response =
        repairs.length > 0
          ? `${greeting}\n\n**Repairs applied:**\n- ✓ **Flush DNS Cache** — DNS cache flushed successfully.\n\n${closing}`
          : `${greeting}\n\nI analyzed your request but no automated actions were run.\n\n${closing}`;
      return {
        message: response,
        source: "local",
        repairs_executed: repairs,
        pending_repairs: msg.includes("slow")
          ? [
              {
                id: "temp-cleanup",
                name: "Clean Temporary Files",
                description: "Remove temporary files",
                purpose: "Free disk space",
                risk_level: "low",
                category: "storage",
                requires_confirmation: true,
                action_kind: "mutating",
                platform: ["linux"],
              },
            ]
          : [],
        verification: repairs.length
          ? {
              health_before: 78,
              health_after: 82,
              issues_before: 2,
              issues_after: 1,
              improved: true,
            }
          : null,
        escalation_case_id: msg.includes("virus") ? "mock-case-1" : null,
        kb_suggestions: [],
      } as T;
    }

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

    case "set_ai_config":
      return undefined as T;

    case "list_knowledge_articles":
      return mockArticles as T;

    case "get_knowledge_article": {
      const id = args?.id as string;
      return (mockArticles.find((a) => a.id === id) || mockArticles[0]) as T;
    }

    case "get_license_info":
      return {
        tier: "free",
        tier_display: "Free",
        features: ["jonathan_ai", "jonathan_auto_repair", "basic_scans", "limited_reports"],
        license_key: null,
        activated_at: null,
        expires_at: null,
        organization: null,
      } as T;

    case "check_feature": {
      const feature = args?.feature as string;
      const freeFeatures = ["jonathan_ai", "jonathan_auto_repair", "basic_scans", "limited_reports"];
      const enterpriseFeatures = [
        "technician_workspace",
        "team_management",
        "enterprise_ai_console",
        "intelligence_console",
        "multi_device",
        "branding",
        "advanced_reporting",
      ];
      const allowed = freeFeatures.includes(feature) || enterpriseFeatures.includes(feature);
      return {
        feature,
        allowed,
        required_tier: freeFeatures.includes(feature)
          ? "free"
          : enterpriseFeatures.includes(feature)
            ? "enterprise"
            : "professional",
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
    case "rotate_provider_api_key":
    case "test_ai_provider_health":
      return {} as T;

    case "list_ai_audit_log":
      return [] as T;

    case "check_for_updates":
      return {
        current_version: "1.1.0",
        latest_version: "1.1.0",
        update_available: false,
        release_notes: "You are running the latest version.",
        download_url: "https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/latest",
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
        message: "Mock PSA webhook delivered.",
      } as T;

    case "export_agent_session_pdf":
      return "/tmp/agent-session.pdf" as T;

    case "list_clients":
    case "list_cases":
    case "list_technician_notes":
      return [] as T;

    case "get_settings":
      return [] as T;

    default:
      console.warn(`Mock: unhandled command ${cmd}`);
      return {} as T;
  }
}
