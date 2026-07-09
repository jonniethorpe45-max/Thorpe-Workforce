import { describe, expect, it, vi } from "vitest";
import { GenesisClient } from "../src/index";

describe("GenesisClient", () => {
  it("posts intent through the gateway", async () => {
    const fetchImpl = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        intent: { type: "calendar.create_event", capability: "calendar.create_event", summary: "hi", entities: {} },
        plan: { steps: [], capability: "calendar.create_event" },
        policy: { decision: "allow", risk_level: "medium", requires_approval: true, reason: "ok" },
        execution: { status: "pending_approval", approval_id: "a1" },
        explanation: "need approval",
      }),
    });

    const client = new GenesisClient({ gatewayUrl: "http://gateway", fetchImpl: fetchImpl as unknown as typeof fetch });
    const result = await client.intent("Schedule a meeting");
    expect(result.execution.approval_id).toBe("a1");
    expect(fetchImpl).toHaveBeenCalledWith(
      "http://gateway/gateway/intent",
      expect.objectContaining({ method: "POST" })
    );
  });
});
