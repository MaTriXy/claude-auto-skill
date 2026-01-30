import { describe, it, expect } from "vitest";
import { createSequenceMatcher } from "../src/core/sequence-matcher";

describe("createSequenceMatcher", () => {
  const matcher = createSequenceMatcher({ minLength: 2, maxLength: 5, minOccurrences: 2 });

  it("finds common subsequences", () => {
    const sequences = [
      ["Read", "Edit", "Bash"],
      ["Read", "Edit", "Bash"],
      ["Grep", "Read", "Edit", "Bash"],
    ];
    const matches = matcher.findCommonSubsequences(sequences);
    expect(matches.length).toBeGreaterThan(0);
    expect(matches[0].occurrences).toBeGreaterThanOrEqual(2);
  });

  it("returns empty for no repeated sequences", () => {
    const sequences = [
      ["Read", "Write"],
      ["Bash", "Grep"],
    ];
    const matches = matcher.findCommonSubsequences(sequences);
    expect(matches).toHaveLength(0);
  });

  it("handles empty input", () => {
    expect(matcher.findCommonSubsequences([])).toHaveLength(0);
  });

  it("respects minLength", () => {
    const m = createSequenceMatcher({ minLength: 3, minOccurrences: 2 });
    const sequences = [
      ["Read", "Edit"],
      ["Read", "Edit"],
    ];
    expect(m.findCommonSubsequences(sequences)).toHaveLength(0);
  });
});
