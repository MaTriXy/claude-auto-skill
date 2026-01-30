import { describe, it, expect } from "vitest";
import { loadConfig, DEFAULT_CONFIG, parseYamlFrontmatter } from "../src/core/config";

describe("loadConfig", () => {
  it("returns default config when no project path given", () => {
    const config = loadConfig();
    expect(config.detection.minOccurrences).toBe(DEFAULT_CONFIG.detection.minOccurrences);
  });

  it("returns default config for non-existent project path", () => {
    const config = loadConfig("/nonexistent/path");
    expect(config.detection.minOccurrences).toBe(DEFAULT_CONFIG.detection.minOccurrences);
  });

  it("has correct default values", () => {
    const config = loadConfig();
    expect(config.detection.minSequenceLength).toBe(DEFAULT_CONFIG.detection.minSequenceLength);
    expect(config.enabled).toBe(true);
  });
});

describe("parseYamlFrontmatter", () => {
  it("parses valid YAML frontmatter", () => {
    const yaml = "---\ndetection:\n  min_occurrences: 5\n---\n";
    const data = parseYamlFrontmatter(yaml);
    expect(data).not.toBeNull();
    expect((data!.detection as Record<string, unknown>).min_occurrences).toBe(5);
  });

  it("returns null for content without frontmatter", () => {
    const data = parseYamlFrontmatter("no frontmatter here");
    expect(data).toBeNull();
  });

  it("returns null for incomplete frontmatter", () => {
    const data = parseYamlFrontmatter("---\nonly one delimiter");
    expect(data).toBeNull();
  });
});
