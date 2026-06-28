import { describe, it, expect } from "vitest";

describe("Billing mock API", () => {
  it("returns billing config", async () => {
    const { mockInvoke } = await import("../src/services/mock");
    const config = await mockInvoke<{
      billing_api_url: string | null;
      stripe_configured: boolean;
      license_api_url: string | null;
    }>("get_billing_config");

    expect(config.stripe_configured).toBe(false);
    expect(config.billing_api_url).toBeNull();
  });

  it("creates a checkout session", async () => {
    const { mockInvoke } = await import("../src/services/mock");
    const session = await mockInvoke<{
      session_id: string;
      checkout_url: string;
      stripe_configured: boolean;
    }>("create_billing_checkout", { tier: "professional" });

    expect(session.session_id).toBeTruthy();
    expect(session.checkout_url).toContain("stripe.com");
  });

  it("polls checkout status with license key", async () => {
    const { mockInvoke } = await import("../src/services/mock");
    const status = await mockInvoke<{
      status: string;
      license_key: string | null;
    }>("get_checkout_status", { sessionId: "mock-checkout-session" });

    expect(status.status).toBe("complete");
    expect(status.license_key).toBeTruthy();
  });
});
