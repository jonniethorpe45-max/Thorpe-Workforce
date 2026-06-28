import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { FeatureRoute } from "../src/components/auth/FeatureRoute";

vi.mock("../src/services/tauri", () => ({
  thorpeApi: {
    checkFeature: vi.fn(),
    getLicenseInfo: vi.fn(),
    getProfile: vi.fn().mockResolvedValue({
      id: "1",
      display_name: "Jordan",
      email: null,
      skill_level: "intermediate",
      role: "user",
      created_at: "",
      updated_at: "",
    }),
  },
}));

import { thorpeApi } from "../src/services/tauri";

function renderFeatureRoute(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route
          path="/intelligence"
          element={
            <FeatureRoute
              feature="intelligence_console"
              title="Intelligence Console"
              description="Requires Enterprise."
            >
              <div>Intelligence content</div>
            </FeatureRoute>
          }
        />
        <Route
          path="/enterprise/ai"
          element={
            <FeatureRoute
              feature="enterprise_ai_console"
              title="Enterprise AI Console"
              description="Requires Enterprise."
            >
              <div>Enterprise AI content</div>
            </FeatureRoute>
          }
        />
        <Route path="/licensing" element={<div>Licensing page</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("FeatureRoute smoke", () => {
  beforeEach(() => {
    vi.mocked(thorpeApi.checkFeature).mockReset();
  });

  it("renders gated content when feature is allowed", async () => {
    vi.mocked(thorpeApi.checkFeature).mockResolvedValue({
      feature: "intelligence_console",
      allowed: true,
      required_tier: "enterprise",
    });

    renderFeatureRoute("/intelligence");
    expect(await screen.findByText("Intelligence content")).toBeTruthy();
  });

  it("shows upgrade prompt when feature is denied", async () => {
    vi.mocked(thorpeApi.checkFeature).mockResolvedValue({
      feature: "enterprise_ai_console",
      allowed: false,
      required_tier: "enterprise",
    });

    renderFeatureRoute("/enterprise/ai");
    await waitFor(() => {
      expect(screen.getByText("Enterprise AI Console")).toBeTruthy();
    });
    expect(screen.getByRole("link", { name: /view licensing/i })).toBeTruthy();
    expect(screen.queryByText("Enterprise AI content")).toBeNull();
  });
});

describe("Critical route registry", () => {
  it("declares all primary desktop paths in App", () => {
    const source = readFileSync(resolve(__dirname, "../src/App.tsx"), "utf8");
    const expectedPaths = [
      'path="/"',
      'path="/jonathan"',
      'path="/scanner"',
      'path="/reports"',
      'path="/repairs"',
      'path="/workspace"',
      'path="/knowledge"',
      'path="/settings"',
      'path="/licensing"',
      'path="/enterprise/ai"',
      'path="/intelligence"',
      'path="/updates"',
    ];
    for (const path of expectedPaths) {
      expect(source).toContain(path);
    }
  });
});
