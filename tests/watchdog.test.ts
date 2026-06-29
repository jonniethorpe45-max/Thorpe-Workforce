import { describe, it, expect } from "vitest";
import { buildWatchdogJonathanPrompt, watchdogEventLabel } from "../src/lib/watchdog";

describe("watchdog helpers", () => {
  it("labels metric event types", () => {
    expect(watchdogEventLabel("high_cpu")).toBe("CPU spike");
    expect(watchdogEventLabel("high_memory")).toBe("Memory pressure");
    expect(watchdogEventLabel("low_disk:/")).toBe("Low disk space");
    expect(watchdogEventLabel("health_threshold")).toBe("Health score");
  });

  it("builds Jonathan handoff prompt", () => {
    const prompt = buildWatchdogJonathanPrompt({
      eventId: "evt-1",
      eventType: "high_cpu",
      message: "CPU usage is 88%",
      healthScore: 68,
    });
    expect(prompt).toContain("Watchdog alert");
    expect(prompt).toContain("68/100");
  });
});
