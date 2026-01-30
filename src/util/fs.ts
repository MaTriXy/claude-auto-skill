/**
 * Common filesystem helpers.
 */

import * as fs from "node:fs";
import * as path from "node:path";
import * as os from "node:os";

/**
 * Ensure a directory exists, creating intermediate directories as needed
 * (equivalent to `mkdir -p`).
 */
export function ensureDir(dir: string): void {
  fs.mkdirSync(dir, { recursive: true });
}

/**
 * Return the default path for the skill-store index database.
 *
 * `~/.claude/auto-skill/index.db`
 */
export function getDefaultDbPath(): string {
  return path.join(os.homedir(), ".claude", "auto-skill", "index.db");
}

/**
 * Return the default directory for auto-generated skills.
 *
 * `~/.claude/skills/auto/`
 */
export function getDefaultSkillsDir(): string {
  return path.join(os.homedir(), ".claude", "skills", "auto");
}

/**
 * Return the auto-skill data directory.
 *
 * `~/.claude/auto-skill/`
 */
export function getAutoSkillDir(): string {
  return path.join(os.homedir(), ".claude", "auto-skill");
}
