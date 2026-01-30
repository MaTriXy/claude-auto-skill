/**
 * Spec Validator - Validates rendered SKILL.md files against the agentskills.io spec.
 *
 * Ensures generated skills conform to the specification:
 * - Name: kebab-case, max 64 chars, matches ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$
 * - Description: max 1024 chars
 * - allowed-tools: must be a YAML list (not comma-separated string)
 * - version: must be present
 * - Frontmatter: valid YAML between --- delimiters
 */

import yaml from "yaml";

import { SPEC_NAME_REGEX, MAX_NAME_LENGTH } from "./path-security";
import type { SpecViolation } from "../types";

/** Max description length per agentskills.io spec. */
export const MAX_DESCRIPTION_LENGTH = 1024;

/**
 * Result of spec validation.
 *
 * Collects violations (errors and warnings) found during validation.
 */
export class SpecValidationResult {
  violations: SpecViolation[] = [];

  /** True if no error-level violations exist. */
  get isValid(): boolean {
    return !this.violations.some((v) => v.severity === "error");
  }

  /** All error-level violations. */
  get errors(): SpecViolation[] {
    return this.violations.filter((v) => v.severity === "error");
  }

  /** All warning-level violations. */
  get warnings(): SpecViolation[] {
    return this.violations.filter((v) => v.severity === "warning");
  }

  /** Add an error-level violation. */
  addError(field: string, message: string): void {
    this.violations.push({ field, message, severity: "error" });
  }

  /** Add a warning-level violation. */
  addWarning(field: string, message: string): void {
    this.violations.push({ field, message, severity: "warning" });
  }
}

/**
 * Extract and parse YAML frontmatter from SKILL.md content.
 *
 * @param content - The full SKILL.md file content.
 * @returns Parsed frontmatter object or null if not found/invalid.
 */
export function extractFrontmatter(
  content: string,
): Record<string, unknown> | null {
  if (!content.startsWith("---")) {
    return null;
  }

  const parts = content.split("---", 3);
  if (parts.length < 3) {
    return null;
  }

  try {
    const parsed = yaml.parse(parts[1]);
    return parsed ?? {};
  } catch {
    return null;
  }
}

/**
 * Validate a SKILL.md file content against the agentskills.io spec.
 *
 * @param content - The full SKILL.md file content.
 * @returns SpecValidationResult with any violations found.
 */
export function validateSkillMd(content: string): SpecValidationResult {
  const result = new SpecValidationResult();

  // Parse frontmatter
  const frontmatter = extractFrontmatter(content);
  if (frontmatter === null) {
    result.addError(
      "frontmatter",
      "Missing or invalid YAML frontmatter (must be between --- delimiters)",
    );
    return result;
  }

  // Validate name
  validateName(frontmatter, result);

  // Validate description
  validateDescription(frontmatter, result);

  // Validate allowed-tools
  validateAllowedTools(frontmatter, result);

  // Validate version
  validateVersion(frontmatter, result);

  return result;
}

// ---------------------------------------------------------------------------
// Internal validators
// ---------------------------------------------------------------------------

function validateName(
  frontmatter: Record<string, unknown>,
  result: SpecValidationResult,
): void {
  const name = frontmatter.name;

  if (!name) {
    result.addError("name", "Missing required field 'name'");
    return;
  }

  if (typeof name !== "string") {
    result.addError("name", `Name must be a string, got ${typeof name}`);
    return;
  }

  if (name.length > MAX_NAME_LENGTH) {
    result.addError(
      "name",
      `Name exceeds ${MAX_NAME_LENGTH} chars (got ${name.length})`,
    );
  }

  if (!SPEC_NAME_REGEX.test(name)) {
    result.addError(
      "name",
      `Name '${name}' does not match spec regex ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$`,
    );
  }
}

function validateDescription(
  frontmatter: Record<string, unknown>,
  result: SpecValidationResult,
): void {
  const desc = frontmatter.description;

  if (!desc) {
    result.addError("description", "Missing required field 'description'");
    return;
  }

  if (typeof desc !== "string") {
    result.addError(
      "description",
      `Description must be a string, got ${typeof desc}`,
    );
    return;
  }

  if (desc.length > MAX_DESCRIPTION_LENGTH) {
    result.addError(
      "description",
      `Description exceeds ${MAX_DESCRIPTION_LENGTH} chars (got ${desc.length})`,
    );
  }
}

function validateAllowedTools(
  frontmatter: Record<string, unknown>,
  result: SpecValidationResult,
): void {
  const tools = frontmatter["allowed-tools"];

  if (tools === undefined || tools === null) {
    // allowed-tools is optional
    return;
  }

  if (typeof tools === "string") {
    result.addError(
      "allowed-tools",
      "Must be a YAML list, not a comma-separated string. " +
        "Use:\n  allowed-tools:\n    - Tool1\n    - Tool2",
    );
    return;
  }

  if (!Array.isArray(tools)) {
    result.addError(
      "allowed-tools",
      `Must be a YAML list, got ${typeof tools}`,
    );
    return;
  }

  for (const item of tools) {
    if (typeof item !== "string") {
      result.addError(
        "allowed-tools",
        `Each tool must be a string, got ${typeof item}: ${item}`,
      );
    }
  }
}

function validateVersion(
  frontmatter: Record<string, unknown>,
  result: SpecValidationResult,
): void {
  const version = frontmatter.version;

  if (version === undefined || version === null) {
    result.addWarning(
      "version",
      "Missing 'version' field (recommended by spec)",
    );
  }
}
