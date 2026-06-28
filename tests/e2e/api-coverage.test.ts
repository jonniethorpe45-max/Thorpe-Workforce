import { describe, it, expect } from "vitest";
import { thorpeApi } from "../../src/services/tauri";

/**
 * Exercises every thorpeApi surface (mock backend in browser E2E).
 * Ensures no invoke command is left unhandled in mock.ts.
 */
describe("E2E API coverage", () => {
  it("covers core app + profile", async () => {
    const app = await thorpeApi.getAppInfo();
    expect(app.version).toBeTruthy();

    const profile = await thorpeApi.getProfile();
    expect(profile.display_name).toBeTruthy();

    const updated = await thorpeApi.updateProfile(profile.display_name, "e2e@test.com", "intermediate");
    expect(updated.email).toBe("e2e@test.com");
  });

  it("covers scanner and reports", async () => {
    const scan = await thorpeApi.runSystemScan();
    expect(scan.health_score).toBeGreaterThan(0);

    const report = await thorpeApi.generateReport(scan.id);
    expect(report.id).toBeTruthy();

    await thorpeApi.listReports();
    await thorpeApi.getReport(report.id);
    await thorpeApi.searchReports("health");
    await thorpeApi.exportReportPdf(report.id, "/tmp/e2e-report.pdf");
  });

  it("covers repairs", async () => {
    const actions = await thorpeApi.listRepairActions();
    expect(actions.length).toBeGreaterThan(0);

    const result = await thorpeApi.executeRepair(actions[0].id, true);
    expect(result.success).toBe(true);

    await thorpeApi.listRepairHistory();
  });

  it("covers jonathan chat and AI config", async () => {
    const chatBase = {
      skill_level: "beginner",
      history: [] as Array<{ role: string; content: string }>,
    };
    const response = await thorpeApi.chatWithJonathan({ ...chatBase, message: "wifi not working" });
    expect(response.message).toBeTruthy();
    expect(response.repairs_executed?.length).toBeGreaterThan(0);

    const slow = await thorpeApi.chatWithJonathan({ ...chatBase, message: "computer is slow" });
    expect(slow.pending_repairs?.length).toBeGreaterThan(0);

    const config = await thorpeApi.getAiConfig();
    await thorpeApi.setAiConfig({ ...config, enabled: false });
    await thorpeApi.getChatHistory(10);
  });

  it("covers knowledge base", async () => {
    const articles = await thorpeApi.listKnowledgeArticles();
    expect(articles.length).toBeGreaterThan(0);
    const article = await thorpeApi.getKnowledgeArticle(articles[0].id);
    expect(article.title).toBeTruthy();
  });

  it("covers licensing and billing", async () => {
    const license = await thorpeApi.getLicenseInfo();
    expect(license.tier).toBeTruthy();

    const activated = await thorpeApi.activateLicense("PRO-DEMO-1234-KEYS-B65C");
    expect(activated.tier).toBe("professional");

    const feature = await thorpeApi.checkFeature("repair_center");
    expect(feature.feature).toBe("repair_center");

    const billing = await thorpeApi.getBillingConfig();
    expect(billing).toBeTruthy();

    const checkout = await thorpeApi.createBillingCheckout("professional");
    expect(checkout.checkout_url).toContain("stripe");

    const status = await thorpeApi.getCheckoutStatus(checkout.session_id);
    expect(status.license_key).toBeTruthy();

    await thorpeApi.openExternalUrl("https://example.com/checkout");
  });

  it("covers enterprise AI console", async () => {
    const dashboard = await thorpeApi.getEnterpriseAiDashboard();
    expect(dashboard.providers.length).toBeGreaterThan(0);

    await thorpeApi.listAiAuditLog(10);
    await thorpeApi.testAiProviderHealth(dashboard.providers[0].id);
    await thorpeApi.upsertAiProvider({
      name: "E2E Provider",
      provider_type: "openai",
      base_url: "https://api.openai.com/v1",
      enabled: true,
      allowed_roles: ["admin"],
    });
    await thorpeApi.upsertAiAgent({
      agent_key: "e2e-agent",
      name: "E2E Agent",
      provider_id: dashboard.providers[0].id,
      model: "gpt-4o-mini",
      enabled: true,
      allowed_roles: ["admin"],
    });
    await thorpeApi.updateAiOrgPolicy({
      cloud_ai_enabled: true,
      default_provider_id: dashboard.providers[0].id,
      monthly_budget_usd: 100,
      monthly_token_limit: 100000,
      enforce_budget: true,
    });
    await thorpeApi.rotateProviderApiKey(dashboard.providers[0].id, "sk-test-key");
  });

  it("covers intelligence console APIs", async () => {
    const synced = await thorpeApi.syncIntelFeed();
    expect(synced).toBeGreaterThanOrEqual(0);

    const intel = await thorpeApi.listIntelItems(10);
    expect(intel.length).toBeGreaterThan(0);

    const packs = await thorpeApi.listRepairPacks();
    expect(packs.length).toBeGreaterThan(0);

    await thorpeApi.installRepairPack(JSON.stringify({ id: "e2e-pack", version: "1.0.0" }));

    await thorpeApi.upsertOrgPlaybook("E2E Playbook", "security", "Content", ["e2e"]);
    await thorpeApi.listOrgPlaybooks();
    await thorpeApi.listAgentSessions(5);
    await thorpeApi.exportAgentSessionPdf("session-1", "/tmp/e2e-session.pdf");
  });

  it("covers watchdog and PSA", async () => {
    const watchdog = await thorpeApi.getWatchdogStatus();
    expect(watchdog.config).toBeTruthy();

    await thorpeApi.updateWatchdogConfig(true, 15, 70, true, true);
    if (watchdog.recent_events[0]) {
      await thorpeApi.acknowledgeWatchdogEvent(watchdog.recent_events[0].id);
    }

    const psa = await thorpeApi.getPsaSettings();
    await thorpeApi.updatePsaSettings(true, "https://psa.example/webhook", "connectwise", "secret");
    await thorpeApi.testPsaWebhook("https://psa.example/webhook", "secret");
    expect(psa).toBeTruthy();
  });

  it("covers technician workspace", async () => {
    const client = await thorpeApi.createClient({
      name: "E2E Client",
      email: "client@test.com",
      phone: null,
      company: "E2E",
      notes: null,
    });
    expect(client.id).toBeTruthy();

    await thorpeApi.updateClient(client.id, { ...client, name: "E2E Updated" });
    await thorpeApi.listClients();

    const supportCase = await thorpeApi.createCase({
      client_id: client.id,
      title: "E2E case",
      description: "Test",
      priority: "high",
      status: "open",
    });
    await thorpeApi.updateCase(supportCase.id, { ...supportCase, status: "in_progress" });
    await thorpeApi.listCases();

    await thorpeApi.addTechnicianNote({
      case_id: supportCase.id,
      report_id: null,
      author: "E2E Tech",
      content: "Investigating",
    });
    await thorpeApi.listTechnicianNotes({ caseId: supportCase.id });
  });

  it("covers settings, updates, and data lifecycle", async () => {
    await thorpeApi.getSettings();
    await thorpeApi.updateSettings("theme", "dark");

    const updates = await thorpeApi.checkForUpdates();
    expect(updates.current_version).toBeTruthy();

    await thorpeApi.deleteAllUserData();
  });
});
