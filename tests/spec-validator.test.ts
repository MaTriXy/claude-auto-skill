import { describe, it, expect } from "vitest";
import { validateSkillMd, extractFrontmatter } from "../src/core/spec-validator";

describe("extractFrontmatter", () => {
  it("extracts valid frontmatter", () => {
    const content = "---\nname: test\ndescription: A test\n---\n# Body";
    const fm = extractFrontmatter(content);
    expect(fm).not.toBeNull();
    expect(fm!.name).toBe("test");
  });
  it("returns null for missing frontmatter", () => {
    expect(extractFrontmatter("no frontmatter")).toBeNull();
  });
  it("returns null for invalid YAML", () => {
    expect(extractFrontmatter("---\n: invalid:\n---\n")).toBeNull();
  });
});

describe("validateSkillMd", () => {
  it("validates a correct SKILL.md", () => {
    const content = "---\nname: my-skill\ndescription: A test skill\nversion: 1.0\n---\n# Body";
    const result = validateSkillMd(content);
    expect(result.isValid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });
  it("rejects missing name", () => {
    const content = "---\ndescription: No name\n---\n# Body";
    const result = validateSkillMd(content);
    expect(result.isValid).toBe(false);
    expect(result.errors.some(e => e.field === "name")).toBe(true);
  });
  it("rejects missing description", () => {
    const content = "---\nname: test\n---\n# Body";
    const result = validateSkillMd(content);
    expect(result.isValid).toBe(false);
  });
  it("warns on missing version", () => {
    const content = "---\nname: test\ndescription: A test\n---\n# Body";
    const result = validateSkillMd(content);
    expect(result.isValid).toBe(true);
    expect(result.warnings.some(w => w.field === "version")).toBe(true);
  });
  it("rejects allowed-tools as string", () => {
    const content = "---\nname: test\ndescription: A test\nallowed-tools: Read,Write\n---\n";
    const result = validateSkillMd(content);
    expect(result.isValid).toBe(false);
    expect(result.errors.some(e => e.field === "allowed-tools")).toBe(true);
  });
  it("accepts allowed-tools as list", () => {
    const content = "---\nname: test\ndescription: A test\nallowed-tools:\n  - Read\n  - Write\n---\n";
    const result = validateSkillMd(content);
    expect(result.errors.filter(e => e.field === "allowed-tools")).toHaveLength(0);
  });
});
