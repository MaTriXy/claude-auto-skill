import { describe, it, expect } from "vitest";
import { createPatternDetector } from "../src/core/pattern-detector";
import type { ToolEvent } from "../src/types";

function makeSession(tools: string[], sessionId: string): ToolEvent[] {
  return tools.map((tool, i) => ({
    id: `evt-${sessionId}-${i}`,
    sessionId,
    toolName: tool,
    timestamp: new Date(Date.now() - (tools.length - i) * 60000).toISOString(),
    success: true,
    toolInput: {},
    projectPath: "/test",
  }));
}

describe("PatternDetector", () => {
  const detector = createPatternDetector();

  it("detects repeated sequences", () => {
    const sessions = [
      makeSession(["Read", "Edit", "Bash"], "s1"),
      makeSession(["Read", "Edit", "Bash"], "s2"),
      makeSession(["Read", "Edit", "Bash"], "s3"),
    ];
    const patterns = detector.detectPatterns(sessions, { minOccurrences: 3 });
    expect(patterns.length).toBeGreaterThan(0);
    expect(patterns[0].occurrenceCount).toBeGreaterThanOrEqual(3);
  });

  it("returns empty for no patterns", () => {
    const sessions = [makeSession(["Read"], "s1")];
    const patterns = detector.detectPatterns(sessions);
    expect(patterns).toHaveLength(0);
  });

  it("filters by confidence", () => {
    const sessions = [
      makeSession(["Read", "Edit", "Bash"], "s1"),
      makeSession(["Read", "Edit", "Bash"], "s2"),
      makeSession(["Read", "Edit", "Bash"], "s3"),
    ];
    const pending = detector.getPendingPatterns(sessions, 0.9);
    // High confidence threshold may filter some out
    for (const p of pending) {
      expect(p.confidence).toBeGreaterThanOrEqual(0.9);
    }
  });
});
