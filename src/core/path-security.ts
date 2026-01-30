/**
 * Path Security - Validates and sanitizes paths for safe filesystem operations.
 *
 * Prevents path traversal attacks, null byte injection, and other filesystem
 * exploits when generating skill names and writing skill files.
 */

import path from "node:path";
import fs from "node:fs";

import { atomicWrite } from "../util/atomic-write";

/** agentskills.io spec regex for skill names. */
export const SPEC_NAME_REGEX = /^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/;

/** Maximum allowed name length (agentskills.io spec). */
export const MAX_NAME_LENGTH = 64;

/** Characters to strip beyond the spec allowlist. */
const UNSAFE_CHARS = /[^a-z0-9-]/g;

/**
 * Sanitize a skill name for safe filesystem and spec-compliant usage.
 *
 * Applies the following transformations:
 * 1. Unicode normalization (NFKD) and ASCII folding
 * 2. Lowercase conversion
 * 3. Replace non-alphanumeric chars (except hyphens) with hyphens
 * 4. Collapse consecutive hyphens
 * 5. Strip leading/trailing hyphens
 * 6. Truncate to MAX_NAME_LENGTH
 * 7. Ensure result matches agentskills.io spec regex
 *
 * @param rawName - The unsanitized name string.
 * @returns A sanitized, spec-compliant kebab-case name.
 * @throws {Error} If the name cannot be sanitized to a valid result.
 */
export function sanitizeName(rawName: string): string {
  if (!rawName) {
    throw new Error("Skill name cannot be empty");
  }

  // Strip null bytes
  let name = rawName.replace(/\0/g, "");

  // Unicode normalize (NFKD) -> ASCII fold (strip non-ASCII)
  name = name.normalize("NFKD").replace(/[^\x00-\x7F]/g, "");

  // Lowercase
  name = name.toLowerCase();

  // Replace path separators and unsafe chars with hyphens
  name = name.replace(/[/\\]/g, "-");
  name = name.replace(UNSAFE_CHARS, "-");

  // Collapse consecutive hyphens
  name = name.replace(/-+/g, "-");

  // Strip leading/trailing hyphens
  name = name.replace(/^-+|-+$/g, "");

  // Truncate to max length (trim at last hyphen to avoid partial words)
  if (name.length > MAX_NAME_LENGTH) {
    name = name.slice(0, MAX_NAME_LENGTH);
    const lastHyphen = name.lastIndexOf("-");
    if (lastHyphen > MAX_NAME_LENGTH / 2) {
      name = name.slice(0, lastHyphen);
    }
    name = name.replace(/-+$/, "");
  }

  if (!name) {
    throw new Error(
      `Skill name '${rawName}' cannot be sanitized to a valid result`,
    );
  }

  if (!SPEC_NAME_REGEX.test(name)) {
    throw new Error(
      `Sanitized name '${name}' does not match spec regex ` +
        "^[a-z0-9]([a-z0-9-]*[a-z0-9])?$",
    );
  }

  return name;
}

/**
 * Check whether a target path is safely contained within an allowed root.
 *
 * Guards against:
 * - Path traversal (../)
 * - Null bytes in path components
 * - Symlink escapes (resolves symlinks before comparison)
 * - Absolute path injection
 *
 * @param target - The path to validate.
 * @param allowedRoot - The directory that must contain `target`.
 * @returns True if target is safely within allowedRoot, false otherwise.
 */
export function isPathSafe(target: string, allowedRoot: string): boolean {
  try {
    // Check for null bytes
    if (target.includes("\0")) {
      return false;
    }

    // Check for suspicious path components
    const parts = target.split(path.sep);
    for (const part of parts) {
      if (part.includes("\0")) {
        return false;
      }
      if (part === "..") {
        return false;
      }
    }

    // Resolve both paths to eliminate symlinks and relative components
    const resolvedTarget = fs.realpathSync(target);
    const resolvedRoot = fs.realpathSync(allowedRoot);

    // Verify containment
    return (
      resolvedTarget === resolvedRoot ||
      resolvedTarget.startsWith(resolvedRoot + path.sep)
    );
  } catch {
    return false;
  }
}

/**
 * Check whether a symlink is safe to create.
 *
 * Ensures both the link location and its target are within allowed boundaries.
 *
 * @param linkPath - Where the symlink will be created.
 * @param targetPath - What the symlink will point to.
 * @param allowedRoot - The root directory that must contain both paths.
 * @returns True if the symlink is safe to create, false otherwise.
 */
export function isSafeSymlink(
  linkPath: string,
  targetPath: string,
  allowedRoot: string,
): boolean {
  if (!isPathSafe(linkPath, allowedRoot)) {
    return false;
  }
  if (!isPathSafe(targetPath, allowedRoot)) {
    return false;
  }
  return true;
}

/**
 * Write content to a file only if the path is safe.
 *
 * Creates parent directories as needed. Uses atomic-write for safety.
 *
 * @param content - The file content to write.
 * @param target - The file path to write to.
 * @param allowedRoot - The directory that must contain `target`.
 * @returns The resolved path of the written file.
 * @throws {Error} If the target path is not safe.
 */
export function safeWrite(
  content: string,
  target: string,
  allowedRoot: string,
): string {
  if (!isPathSafe(target, allowedRoot)) {
    throw new Error(
      `Unsafe path: ${target} is not within allowed root ${allowedRoot}`,
    );
  }

  const resolved = fs.realpathSync(target);
  fs.mkdirSync(path.dirname(resolved), { recursive: true });
  atomicWrite(resolved, content);
  return resolved;
}
