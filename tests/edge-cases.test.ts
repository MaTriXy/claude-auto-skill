import { describe, it, expect } from "vitest";
import { sanitizeName } from "../src/core/path-security";
import { validateSkillMd } from "../src/core/spec-validator";

describe("edge cases", () => {
  it("handles unicode in skill names", () => {
    const name = sanitizeName("caf\u00e9-skill");
    expect(name).toBeTruthy();
    expect(name.length).toBeGreaterThan(0);
  });

  it("handles very long descriptions", () => {
    const desc = "a".repeat(2000);
    const content = `---\nname: test\ndescription: ${desc}\n---\n`;
    const result = validateSkillMd(content);
    expect(result.errors.some(e => e.field === "description")).toBe(true);
  });

  it("handles empty SKILL.md", () => {
    const result = validateSkillMd("");
    expect(result.isValid).toBe(false);
  });

  it("handles only frontmatter delimiters", () => {
    const result = validateSkillMd("---\n---\n");
    expect(result.isValid).toBe(false);
  });
});
