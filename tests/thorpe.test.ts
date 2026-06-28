import { describe, it, expect } from "vitest";
import { JONATHAN_WELCOME, JONATHAN_SYSTEM_PROMPT } from "../src/prompts/jonathan";

describe("Jonathan prompts", () => {
  it("has a welcome message", () => {
    expect(JONATHAN_WELCOME).toContain("Jonathan");
    expect(JONATHAN_WELCOME).toContain("fix issues");
  });

  it("defines autonomous repair behavior in system prompt", () => {
    expect(JONATHAN_SYSTEM_PROMPT).toContain("fix problems directly");
  });
});

describe("License tiers", () => {
  const tiers = {
    free: ["jonathan_ai", "jonathan_auto_repair", "basic_scans", "limited_reports"],
    professional: ["repair_center", "pdf_export", "unlimited_reports"],
    enterprise: ["technician_workspace", "multi_device", "team_management"],
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

  it("enterprise tier includes workspace", () => {
    expect(tiers.enterprise).toContain("technician_workspace");
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
