import { describe, it, expect, vi } from "vitest";
import { isTelemetryDisabled, track } from "../src/core/telemetry";

describe("telemetry", () => {
  it("respects DO_NOT_TRACK", () => {
    const orig = process.env.DO_NOT_TRACK;
    process.env.DO_NOT_TRACK = "1";
    expect(isTelemetryDisabled()).toBe(true);
    process.env.DO_NOT_TRACK = orig;
  });

  it("respects AUTO_SKILL_NO_TELEMETRY", () => {
    const orig = process.env.AUTO_SKILL_NO_TELEMETRY;
    process.env.AUTO_SKILL_NO_TELEMETRY = "1";
    expect(isTelemetryDisabled()).toBe(true);
    process.env.AUTO_SKILL_NO_TELEMETRY = orig;
  });

  it("track never throws", () => {
    expect(() => track("test_event", { value: 1 })).not.toThrow();
  });
});
