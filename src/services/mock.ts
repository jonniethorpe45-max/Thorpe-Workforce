import type { KnowledgeArticle, SystemScanResult } from "./types";
import { JONATHAN_WELCOME } from "../prompts/jonathan";

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
        version: "1.0.0",
        platform: "linux",
        data_dir: "/tmp/thorpe",
      } as T;

    case "get_profile":
      return {
        id: "mock-profile",
        display_name: "User",
        email: null,
        skill_level: "beginner",
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
      let response = JONATHAN_WELCOME;
      if (msg.includes("wifi") || msg.includes("network")) {
        response =
          "Let's troubleshoot your network. Try toggling Wi-Fi, restarting your router, and flushing DNS cache.";
      }
      return { message: response, source: "local" } as T;
    }

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
        features: ["jonathan_ai", "basic_scans", "limited_reports"],
        license_key: null,
        activated_at: null,
        expires_at: null,
        organization: null,
      } as T;

    case "check_feature": {
      const feature = args?.feature as string;
      const freeFeatures = ["jonathan_ai", "basic_scans", "limited_reports"];
      return {
        feature,
        allowed: freeFeatures.includes(feature),
        required_tier: freeFeatures.includes(feature) ? "free" : "professional",
      } as T;
    }

    case "check_for_updates":
      return {
        current_version: "1.0.0",
        latest_version: "1.0.0",
        update_available: false,
        release_notes: "You are running the latest version.",
        download_url: "https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/latest",
      } as T;

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
