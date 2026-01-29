import { describe, it, expect } from "vitest";
import { formatTable, formatJson, formatConfidenceBar, formatMarkdown, formatSkills } from "../src/formatter";

describe("formatTable", () => {
  it("formats a simple table", () => {
    const result = formatTable(["Name", "Value"], [["foo", "bar"], ["baz", "qux"]]);
    expect(result).toContain("Name");
    expect(result).toContain("foo");
  });
  it("handles empty rows", () => {
    expect(formatTable(["A"], [])).toBe("(no data)");
  });
});

describe("formatConfidenceBar", () => {
  it("formats full bar", () => {
    expect(formatConfidenceBar(1.0, 10)).toBe("##########");
  });
  it("formats half bar", () => {
    expect(formatConfidenceBar(0.5, 10)).toBe("#####.....");
  });
  it("formats empty bar", () => {
    expect(formatConfidenceBar(0, 10)).toBe("..........");
  });
});

describe("formatSkills", () => {
  it("formats as JSON", () => {
    const result = formatSkills([{ name: "test" }], { format: "json" });
    expect(JSON.parse(result)).toHaveLength(1);
  });
  it("formats as text", () => {
    const result = formatSkills([{ name: "test", description: "A test" }], { format: "text" });
    expect(result).toContain("test");
  });
});
