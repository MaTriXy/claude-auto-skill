import { describe, it, expect } from "vitest";
import { loadConfig, DEFAULT_CONFIG } from "../src/core/config";

describe("loadConfig", () => {
  it("returns default config for empty input", () => {
    const config = loadConfig("");
    expect(config.detection.minOccurrences).toBe(DEFAULT_CONFIG.detection.minOccurrences);
  });

  it("parses valid YAML config", () => {
    const yaml = "---\ndetection:\n  min_occurrences: 5\n---\n";
    const config = loadConfig(yaml);
    expect(config.detection.minOccurrences).toBe(5);
  });

  it("merges with defaults", () => {
    const yaml = "---\ndetection:\n  min_occurrences: 5\n---\n";
    const config = loadConfig(yaml);
    expect(config.detection.minSequenceLength).toBe(DEFAULT_CONFIG.detection.minSequenceLength);
  });
});
