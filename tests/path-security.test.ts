import { describe, it, expect } from "vitest";
import { sanitizeName, isPathSafe, SPEC_NAME_REGEX, MAX_NAME_LENGTH } from "../src/core/path-security";

describe("sanitizeName", () => {
  it("converts to lowercase kebab-case", () => {
    expect(sanitizeName("MySkill Name")).toBe("myskill-name");
  });
  it("removes special characters", () => {
    expect(sanitizeName("test@#$%skill")).toBe("testskill");
  });
  it("truncates to max length", () => {
    const long = "a".repeat(100);
    expect(sanitizeName(long).length).toBeLessThanOrEqual(MAX_NAME_LENGTH);
  });
  it("handles empty string", () => {
    expect(sanitizeName("")).toBe("unnamed-skill");
  });
  it("collapses multiple hyphens", () => {
    expect(sanitizeName("a---b")).toBe("a-b");
  });
  it("strips leading/trailing hyphens", () => {
    expect(sanitizeName("-test-")).toBe("test");
  });
});

describe("isPathSafe", () => {
  it("allows paths within root", () => {
    expect(isPathSafe("/home/user/skills/test", "/home/user")).toBe(true);
  });
  it("rejects path traversal", () => {
    expect(isPathSafe("/home/user/../etc/passwd", "/home/user")).toBe(false);
  });
  it("rejects absolute path outside root", () => {
    expect(isPathSafe("/etc/passwd", "/home/user")).toBe(false);
  });
});

describe("SPEC_NAME_REGEX", () => {
  it("matches valid names", () => {
    expect(SPEC_NAME_REGEX.test("my-skill")).toBe(true);
    expect(SPEC_NAME_REGEX.test("a")).toBe(true);
    expect(SPEC_NAME_REGEX.test("test123")).toBe(true);
  });
  it("rejects invalid names", () => {
    expect(SPEC_NAME_REGEX.test("My-Skill")).toBe(false);
    expect(SPEC_NAME_REGEX.test("-test")).toBe(false);
    expect(SPEC_NAME_REGEX.test("")).toBe(false);
  });
});
