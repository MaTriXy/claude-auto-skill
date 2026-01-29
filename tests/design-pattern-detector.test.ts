import { describe, it, expect } from "vitest";
import { createDesignPatternDetector } from "../src/core/design-pattern-detector";

describe("DesignPatternDetector", () => {
  const detector = createDesignPatternDetector();

  it("detects TDD workflow pattern", () => {
    const toolSequence = ["Write", "Bash", "Edit", "Bash"];
    const result = detector.detectWorkflowPattern(toolSequence);
    expect(result).not.toBeNull();
    expect(result!.name).toContain("TDD");
  });

  it("detects Debug-Systematic pattern", () => {
    const toolSequence = ["Read", "Grep", "Bash", "Edit"];
    const result = detector.detectWorkflowPattern(toolSequence);
    expect(result).not.toBeNull();
  });

  it("returns null for no pattern match", () => {
    const result = detector.detectWorkflowPattern(["Unknown"]);
    expect(result).toBeNull();
  });

  it("suggests patterns for context", () => {
    const suggestions = detector.suggestPatternsForContext("debug", "authentication");
    expect(suggestions.length).toBeGreaterThan(0);
  });
});
