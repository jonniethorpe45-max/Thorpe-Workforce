import React from "react";
import { render, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AppRoutes } from "../../src/App";

export const ROUTES = [
  { path: "/", heading: /welcome back/i },
  { path: "/scanner", heading: /system health scanner/i },
  { path: "/reports", heading: /diagnostic reports/i },
  { path: "/repairs", heading: /repair center/i },
  { path: "/workspace", heading: /technician workspace/i },
  { path: "/jonathan", heading: /jonathan/i },
  { path: "/knowledge", heading: /knowledge base/i },
  { path: "/settings", heading: /^settings$/i },
  { path: "/licensing", heading: /licensing & subscription/i },
  { path: "/updates", heading: /update manager/i },
  { path: "/enterprise/ai", heading: /enterprise ai console/i },
  { path: "/intelligence", heading: /intelligence console/i },
] as const;

export function renderApp(initialPath = "/") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AppRoutes />
    </MemoryRouter>
  );
}

export async function waitForAppReady() {
  await waitFor(
    () => {
      expect(document.body.textContent?.length ?? 0).toBeGreaterThan(20);
    },
    { timeout: 5000 }
  );
}

export const enterpriseLicense = {
  tier: "enterprise",
  tier_display: "Enterprise",
  features: [
    "jonathan_ai",
    "repair_center",
    "technician_workspace",
    "enterprise_ai_console",
    "intelligence_console",
  ],
  license_key: "ENT-E2E-0001-TEST-0000",
  activated_at: new Date().toISOString(),
  expires_at: null,
  organization: "E2E Org",
};

export const professionalLicense = {
  tier: "professional",
  tier_display: "Professional",
  features: ["jonathan_ai", "repair_center", "pdf_export", "unlimited_reports"],
  license_key: "PRO-E2E-0001-TEST-0000",
  activated_at: new Date().toISOString(),
  expires_at: null,
  organization: null,
};

const enterpriseFeatures = new Set([
  "repair_center",
  "technician_workspace",
  "enterprise_ai_console",
  "intelligence_console",
  "pdf_export",
  "unlimited_reports",
]);

export function allowEnterpriseFeatures() {
  return async (feature: string) => ({
    feature,
    allowed: enterpriseFeatures.has(feature) || feature.startsWith("jonathan"),
    required_tier: enterpriseFeatures.has(feature) ? "enterprise" : "free",
  });
}
