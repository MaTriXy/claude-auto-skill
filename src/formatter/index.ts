/**
 * Formatter - Multi-format output for CLI and API responses.
 *
 * Supports: json, table, markdown, plain text.
 * Inspired by qmd's formatter pattern.
 */

export type OutputFormat = "json" | "table" | "markdown" | "text";

export interface FormatOptions {
  format?: OutputFormat;
  compact?: boolean;
  noColor?: boolean;
}

/** Format a list of records as a table. */
export function formatTable(
  headers: string[],
  rows: (string | number)[][],
  opts?: { compact?: boolean }
): string {
  if (rows.length === 0) return "(no data)";

  // Calculate column widths
  const widths = headers.map((h, i) => {
    const maxData = Math.max(...rows.map(r => String(r[i] ?? "").length));
    return Math.max(h.length, maxData);
  });

  const lines: string[] = [];

  // Header
  const headerLine = headers.map((h, i) => h.padEnd(widths[i])).join("  ");
  lines.push(headerLine);
  lines.push(widths.map(w => "-".repeat(w)).join("  "));

  // Rows
  for (const row of rows) {
    const line = row.map((cell, i) => String(cell ?? "").padEnd(widths[i])).join("  ");
    lines.push(line);
  }

  return lines.join("\n");
}

/** Format data as JSON. */
export function formatJson(data: unknown, compact?: boolean): string {
  return JSON.stringify(data, null, compact ? 0 : 2);
}

/** Format a confidence value as a bar. */
export function formatConfidenceBar(confidence: number, width: number = 10): string {
  const filled = Math.round(confidence * width);
  return "#".repeat(filled) + ".".repeat(width - filled);
}

/** Format data as markdown. */
export function formatMarkdown(
  title: string,
  headers: string[],
  rows: (string | number)[][]
): string {
  const lines: string[] = [];

  lines.push(`## ${title}\n`);

  if (rows.length === 0) {
    lines.push("_No data_\n");
    return lines.join("\n");
  }

  // Table header
  lines.push("| " + headers.join(" | ") + " |");
  lines.push("| " + headers.map(() => "---").join(" | ") + " |");

  // Rows
  for (const row of rows) {
    lines.push("| " + row.map(c => String(c ?? "")).join(" | ") + " |");
  }

  lines.push("");
  return lines.join("\n");
}

/** Format skills for display. */
export function formatSkills(
  skills: Array<{ name: string; description?: string; source?: string; confidence?: number; tags?: string[] }>,
  opts?: FormatOptions
): string {
  const format = opts?.format || "text";

  if (format === "json") {
    return formatJson(skills, opts?.compact);
  }

  if (format === "markdown") {
    return formatMarkdown(
      "Skills",
      ["Name", "Source", "Confidence", "Tags"],
      skills.map(s => [
        s.name,
        s.source || "local",
        s.confidence !== undefined ? `${(s.confidence * 100).toFixed(0)}%` : "-",
        (s.tags || []).join(", "),
      ])
    );
  }

  if (format === "table") {
    return formatTable(
      ["Name", "Source", "Confidence", "Tags"],
      skills.map(s => [
        s.name,
        s.source || "local",
        s.confidence !== undefined ? `${(s.confidence * 100).toFixed(0)}%` : "-",
        (s.tags || []).join(", "),
      ])
    );
  }

  // Plain text
  const lines: string[] = [];
  for (let i = 0; i < skills.length; i++) {
    const s = skills[i];
    const bar = s.confidence !== undefined ? ` [${formatConfidenceBar(s.confidence)}]` : "";
    lines.push(`${i + 1}. ${s.name}${bar}`);
    if (s.description) lines.push(`   ${s.description}`);
    if (s.source) lines.push(`   Source: ${s.source}`);
    if (s.tags?.length) lines.push(`   Tags: ${s.tags.join(", ")}`);
    lines.push("");
  }
  return lines.join("\n");
}

/** Format a single value output (for simple commands). */
export function formatOutput(data: unknown, opts?: FormatOptions): string {
  if (opts?.format === "json") {
    return formatJson(data, opts?.compact);
  }
  if (typeof data === "string") return data;
  return JSON.stringify(data, null, 2);
}
