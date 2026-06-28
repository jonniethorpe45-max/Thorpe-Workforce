import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor, fireEvent, act } from "@testing-library/react";
import {
  allowEnterpriseFeatures,
  enterpriseLicense,
  professionalLicense,
  renderApp,
  waitForAppReady,
} from "./helpers";
import { thorpeApi } from "../../src/services/tauri";

describe("E2E user flows", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("dashboard loads scan summary and navigation", async () => {
    renderApp("/");
    await waitForAppReady();
    await waitFor(() => {
      expect(screen.getByText(/welcome back, alex/i)).toBeTruthy();
    });
    expect(screen.getByRole("link", { name: /system health/i })).toBeTruthy();
    expect(screen.getByRole("link", { name: /jonathan ai/i })).toBeTruthy();
  });

  it("system scanner: consent → scan → health score", async () => {
    renderApp("/scanner");
    await waitForAppReady();

    const consent = screen.getByRole("checkbox");
    fireEvent.click(consent);

    const scanButton = screen.getByRole("button", { name: /run system scan/i });
    fireEvent.click(scanButton);

    await waitFor(
      () => {
        expect(screen.getByText(/82/)).toBeTruthy();
      },
      { timeout: 5000 }
    );
  });

  it("jonathan: sends message and receives repair response", async () => {
    renderApp("/jonathan");
    await waitForAppReady();

    const input = screen.getByPlaceholderText(/describe your it issue/i);
    fireEvent.change(input, { target: { value: "wifi not working" } });
    fireEvent.keyDown(input, { key: "Enter" });

    await waitFor(
      () => {
        expect(screen.getByText(/flush dns cache/i)).toBeTruthy();
      },
      { timeout: 10000 }
    );
  });

  it("jonathan: slow message shows pending repair approval", async () => {
    renderApp("/jonathan");
    await waitForAppReady();

    const input = screen.getByPlaceholderText(/describe your it issue/i);
    fireEvent.change(input, { target: { value: "my computer is slow" } });
    fireEvent.keyDown(input, { key: "Enter" });

    await waitFor(
      () => {
        expect(screen.getByText(/clean temporary files/i)).toBeTruthy();
      },
      { timeout: 10000 }
    );
  });

  it("licensing: activates a professional license key", async () => {
    renderApp("/licensing");
    await waitForAppReady();

    const input = screen.getByPlaceholderText(/PRO-XXXX/i);
    fireEvent.change(input, { target: { value: "PRO-DEMO-1234-KEYS-B65C" } });
    fireEvent.click(screen.getByRole("button", { name: /^activate$/i }));

    await waitFor(
      () => {
        expect(screen.getAllByText(/^Professional$/).length).toBeGreaterThan(0);
      },
      { timeout: 8000 }
    );
  });

  it("licensing: billing checkout polling activates license", async () => {
    vi.spyOn(thorpeApi, "getBillingConfig").mockResolvedValue({
      billing_api_url: "https://license.test",
      stripe_configured: true,
      license_api_url: null,
    });

    renderApp("/licensing");
    await waitForAppReady();

    await waitFor(() => {
      expect(screen.getAllByRole("button", { name: /^subscribe$/i }).length).toBeGreaterThan(0);
    });

    const subscribeButtons = screen.getAllByRole("button", { name: /^subscribe$/i });
    fireEvent.click(subscribeButtons[0]);

    await waitFor(
      () => {
        expect(screen.getAllByText(/^Professional$/).length).toBeGreaterThan(0);
      },
      { timeout: 15000 }
    );
  });

  it("repair center loads actions with professional license", async () => {
    vi.spyOn(thorpeApi, "getLicenseInfo").mockResolvedValue(professionalLicense);
    vi.spyOn(thorpeApi, "checkFeature").mockImplementation(async (feature) => ({
      feature,
      allowed: feature === "repair_center" || feature.startsWith("jonathan"),
      required_tier: feature === "repair_center" ? "professional" : "free",
    }));

    renderApp("/repairs");
    await waitForAppReady();

    await waitFor(
      () => {
        expect(screen.getByText(/clean temporary files/i)).toBeTruthy();
      },
      { timeout: 5000 }
    );
  });

  it("knowledge base lists articles", async () => {
    renderApp("/knowledge");
    await waitForAppReady();

    await waitFor(() => {
      expect(screen.getByText(/slow windows startup/i)).toBeTruthy();
      expect(screen.getByText(/dns resolution failures/i)).toBeTruthy();
    });
  });

  it("settings loads profile and watchdog sections", async () => {
    renderApp("/settings");
    await waitForAppReady();

    await waitFor(
      () => {
        expect(screen.getByDisplayValue(/alex johnson/i)).toBeTruthy();
      },
      { timeout: 8000 }
    );
    expect(screen.getByRole("heading", { name: /proactive watchdog/i })).toBeTruthy();
    expect(screen.getByRole("heading", { name: /psa integration/i })).toBeTruthy();
  });

  it("update manager checks for updates", async () => {
    renderApp("/updates");
    await waitForAppReady();

    await waitFor(() => {
      expect(screen.getByText(/1\.1\.0/)).toBeTruthy();
    });
    expect(screen.getByRole("button", { name: /check for updates/i })).toBeTruthy();
  });

  it("enterprise AI console renders with enterprise license", async () => {
    vi.spyOn(thorpeApi, "getLicenseInfo").mockResolvedValue(enterpriseLicense);
    vi.spyOn(thorpeApi, "checkFeature").mockImplementation(async (feature) => ({
      feature,
      allowed: true,
      required_tier: "enterprise",
    }));

    renderApp("/enterprise/ai");
    await waitForAppReady();

    await waitFor(
      () => {
        expect(screen.getByText(/monthly spend/i)).toBeTruthy();
        expect(screen.getByRole("heading", { name: "OpenAI", level: 3 })).toBeTruthy();
      },
      { timeout: 12000 }
    );
  });

  it("intelligence console renders tabs with enterprise license", async () => {
    vi.spyOn(thorpeApi, "getLicenseInfo").mockResolvedValue(enterpriseLicense);
    vi.spyOn(thorpeApi, "checkFeature").mockImplementation(allowEnterpriseFeatures());

    renderApp("/intelligence");
    await waitForAppReady();

    await waitFor(
      () => {
        expect(screen.getByRole("heading", { name: /intelligence console/i })).toBeTruthy();
        expect(screen.getByRole("button", { name: /threat intel/i })).toBeTruthy();
        expect(screen.getByRole("button", { name: /repair packs/i })).toBeTruthy();
      },
      { timeout: 10000 }
    );
  });

  it("technician workspace accessible with enterprise license", async () => {
    vi.spyOn(thorpeApi, "getLicenseInfo").mockResolvedValue(enterpriseLicense);
    vi.spyOn(thorpeApi, "checkFeature").mockImplementation(allowEnterpriseFeatures());

    renderApp("/workspace");
    await waitForAppReady();

    await waitFor(
      () => {
        expect(screen.getByRole("heading", { name: /technician workspace/i })).toBeTruthy();
        expect(screen.getByRole("button", { name: /new case/i })).toBeTruthy();
      },
      { timeout: 10000 }
    );
  });

  it("feature gates block enterprise routes on free tier", async () => {
    renderApp("/intelligence");
    await waitForAppReady();

    await waitFor(
      () => {
        expect(screen.getByRole("link", { name: /view licensing/i })).toBeTruthy();
      },
      { timeout: 10000 }
    );
    expect(screen.queryByRole("button", { name: /threat intel/i })).toBeNull();
  });

  it("global search navigates to knowledge base", async () => {
    renderApp("/");
    await waitForAppReady();

    const searchInput = screen.getByPlaceholderText(/search knowledge base/i);
    fireEvent.change(searchInput, { target: { value: "dns" } });
    fireEvent.submit(searchInput.closest("form")!);

    await waitFor(
      () => {
        expect(screen.getByRole("heading", { name: /knowledge base/i })).toBeTruthy();
      },
      { timeout: 8000 }
    );
  });
});
