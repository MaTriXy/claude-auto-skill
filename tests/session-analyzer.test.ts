import { describe, it, expect } from "vitest";
import { createSessionAnalyzer } from "../src/core/session-analyzer";
import type { ToolEvent } from "../src/types";

function makeEvent(tool: string, ts: number, success = true): ToolEvent {
  return {
    id: `evt-${ts}`,
    sessionId: "sess-1",
    toolName: tool,
    timestamp: new Date(ts * 1000).toISOString(),
    success,
    toolInput: {},
    projectPath: "/test",
  };
}

describe("SessionAnalyzer", () => {
  const analyzer = createSessionAnalyzer();

  it("analyzes a session with events", () => {
    const events = [
      makeEvent("Read", 100),
      makeEvent("Edit", 101),
      makeEvent("Bash", 102),
    ];
    const ctx = analyzer.analyzeSession("sess-1", events);
    expect(ctx.sessionId).toBe("sess-1");
    expect(ctx.turns.length).toBeGreaterThan(0);
  });

  it("handles empty events", () => {
    const ctx = analyzer.analyzeSession("empty", []);
    expect(ctx.turns).toHaveLength(0);
  });

  it("calculates success indicators", () => {
    const events = [
      makeEvent("Read", 100, true),
      makeEvent("Bash", 101, false),
      makeEvent("Edit", 102, true),
    ];
    const ctx = analyzer.analyzeSession("sess-1", events);
    const indicators = ctx.successIndicators as Record<string, number>;
    expect(indicators.tool_success_rate).toBeCloseTo(2 / 3, 1);
  });
});
