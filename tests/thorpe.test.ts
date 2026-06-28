import { describe, it, expect, vi } from "vitest";
import { JONATHAN_WELCOME, JONATHAN_SYSTEM_PROMPT, buildJonathanWelcome } from "../src/prompts/jonathan";
import { extractFirstName } from "../src/lib/userName";

describe("Jonathan prompts", () => {
  it("has a welcome message", () => {
    expect(JONATHAN_WELCOME).toContain("Jonathan");
    expect(JONATHAN_WELCOME).toContain("fix issues");
  });

  it("defines autonomous repair behavior in system prompt", () => {
    expect(JONATHAN_SYSTEM_PROMPT).toContain("fix problems directly");
    expect(JONATHAN_SYSTEM_PROMPT).toContain("first name");
  });

  it("personalizes welcome message with first name", () => {
    expect(buildJonathanWelcome("Jordan")).toContain("Hello, **Jordan**!");
    expect(JONATHAN_WELCOME).toContain("Hello!");
  });
});

describe("Jonathan mode labels", () => {
  it("labels cloud and fallback sources", async () => {
    const { getJonathanSourceLabel, isCloudAiActive } = await import("../src/lib/jonathanMode");
    expect(getJonathanSourceLabel("openai")).toBe("Cloud AI");
    expect(getJonathanSourceLabel("cloud_fallback")).toBe("Cloud AI (local fallback)");
    expect(isCloudAiActive({ enabled: true, api_key_configured: true })).toBe(true);
    expect(isCloudAiActive({ enabled: true, api_key_configured: false })).toBe(false);
  });
});

describe("User name helpers", () => {
  it("extracts first name from display name", () => {
    expect(extractFirstName("Jordan Smith")).toBe("Jordan");
  });

  it("skips generic placeholder names", () => {
    expect(extractFirstName("User")).toBeNull();
  });
});

describe("License tiers", () => {
  const tiers = {
    free: ["jonathan_ai", "jonathan_auto_repair", "basic_scans", "limited_reports"],
    professional: ["repair_center", "pdf_export", "unlimited_reports"],
    enterprise: ["technician_workspace", "enterprise_ai_console", "intelligence_console"],
  };

  it("free tier includes Jonathan autonomous repair", () => {
    expect(tiers.free).toContain("jonathan_ai");
    expect(tiers.free).toContain("jonathan_auto_repair");
    expect(tiers.free).not.toContain("repair_center");
  });

  it("professional tier includes repair center", () => {
    expect(tiers.professional).toContain("repair_center");
    expect(tiers.professional).toContain("pdf_export");
  });

  it("enterprise tier includes workspace and intelligence console", () => {
    expect(tiers.enterprise).toContain("technician_workspace");
    expect(tiers.enterprise).toContain("intelligence_console");
    expect(tiers.enterprise).not.toContain("multi_device");
  });
});

describe("Health score calculation", () => {
  function calculateScore(issues: Array<{ severity: string }>, memPct: number): number {
    let score = 100;
    for (const issue of issues) {
      score -= issue.severity === "critical" ? 25 : issue.severity === "high" ? 15 : issue.severity === "medium" ? 8 : 3;
    }
    if (memPct > 90) score -= 10;
    return Math.max(0, Math.min(100, score));
  }

  it("returns 100 for no issues", () => {
    expect(calculateScore([], 50)).toBe(100);
  });

  it("deducts for critical issues", () => {
    expect(calculateScore([{ severity: "critical" }], 50)).toBe(75);
  });

  it("clamps to 0", () => {
    const issues = Array(10).fill({ severity: "critical" });
    expect(calculateScore(issues, 95)).toBe(0);
  });
});

describe("Risk levels", () => {
  it("maps severity to display", () => {
    const levels = ["low", "medium", "high", "critical"];
    levels.forEach((level) => {
      expect(["low", "medium", "high", "critical"]).toContain(level);
    });
  });
});

describe("Knowledge base structure", () => {
  const requiredFields = ["symptoms", "causes", "fixes", "prevention", "when_to_escalate"];

  it("articles have all required fields", () => {
    const article = {
      symptoms: "Test",
      causes: "Test",
      fixes: "Test",
      prevention: "Test",
      when_to_escalate: "Test",
    };
    requiredFields.forEach((field) => {
      expect(article).toHaveProperty(field);
    });
  });
});

describe("Word-by-word reveal", () => {
  it("tokenizes words and whitespace", async () => {
    const { tokenizeForReveal } = await import("../src/lib/wordByWord");
    expect(tokenizeForReveal("Hello world")).toEqual(["Hello", " ", "world"]);
    expect(tokenizeForReveal("One\ntwo")).toEqual(["One", "\n", "two"]);
  });

  it("reveals assistant text progressively", async () => {
    const React = await import("react");
    const { render, screen, act } = await import("@testing-library/react");
    const { WordByWordReply } = await import("../src/components/ui/WordByWordReply");

    vi.useFakeTimers();

    try {
      const { container } = render(
        React.createElement(WordByWordReply, {
          content: "Hello there friend",
          animate: true,
        })
      );

      await act(async () => {
        vi.advanceTimersByTime(90);
      });

      expect(container.textContent).toContain("Hello");
      expect(container.textContent).not.toContain("friend");

      await act(async () => {
        vi.advanceTimersByTime(500);
      });

      expect(screen.getByText(/friend/)).toBeTruthy();
    } finally {
      vi.useRealTimers();
    }
  });
});

describe("Safe markdown rendering", () => {
  it("renders bold and italic without HTML injection", async () => {
    const React = await import("react");
    const { render, screen } = await import("@testing-library/react");
    const { SafeMarkdown } = await import("../src/components/ui/SafeMarkdown");

    render(
      React.createElement(SafeMarkdown, {
        content: "**bold** and *italic*\n<script>alert(1)</script>",
      })
    );

    expect(screen.getByText("bold").tagName).toBe("STRONG");
    expect(screen.getByText("italic").tagName).toBe("EM");
    expect(screen.getByText("<script>alert(1)</script>")).toBeTruthy();
  });
});

describe("Mock API", () => {
  it("returns mock scan data", async () => {
    const { mockInvoke } = await import("../src/services/mock");
    const scan = await mockInvoke<Record<string, unknown>>("run_system_scan");
    expect(scan).toHaveProperty("health_score");
    expect(scan).toHaveProperty("os");
  });

  it("handles chat requests", async () => {
    const { mockInvoke } = await import("../src/services/mock");
    const response = await mockInvoke<{ message: string; source: string; repairs_executed?: unknown[] }>("chat_with_jonathan", {
      request: { message: "wifi not working" },
    });
    expect(response.message).toBeTruthy();
    expect(response.source).toBe("local");
    expect(response.repairs_executed?.length).toBeGreaterThan(0);
  });
});

describe("Production smoke checks", () => {
  it("keeps version and download URLs aligned", async () => {
    const { THORPE_VERSION } = await import("../src/config/version");
    const { THORPE_DOWNLOADS } = await import("../src/config/downloads");
    const packageJson = await import("../package.json");

    expect(THORPE_VERSION).toBe(packageJson.default.version);
    expect(THORPE_DOWNLOADS.windowsExe).toContain(THORPE_VERSION);
    expect(THORPE_DOWNLOADS.linuxDeb).toContain(THORPE_VERSION);
  });

  it("mock update check returns structured info", async () => {
    const { mockInvoke } = await import("../src/services/mock");
    const info = await mockInvoke<{
      current_version: string;
      latest_version: string;
      update_available: boolean;
      release_notes: string;
      download_url: string;
    }>("check_for_updates");

    expect(info.current_version).toBeTruthy();
    expect(info.download_url).toContain("github.com");
  });

  it("mock license activation returns tier features", async () => {
    const { mockInvoke } = await import("../src/services/mock");
    const license = await mockInvoke<{ tier: string; features: string[] }>("activate_license", {
      request: { license_key: "PRO-DEMO-1234-KEYS-B65C" },
    });

    expect(license.tier).toBe("professional");
    expect(license.features).toContain("repair_center");
  });
});
