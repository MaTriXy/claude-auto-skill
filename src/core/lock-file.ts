/**
 * Lock File — Tracks installed skills with integrity verification.
 *
 * Maintains a skills.lock.json file that records:
 * - Installed skills and their metadata
 * - SHA-256 content hashes for integrity verification
 * - Version counter for change tracking
 * - Atomic writes to prevent corruption
 *
 * Ported from Python core/lock_file.py.
 * Key changes:
 * - Uses node:crypto for SHA-256
 * - Uses writeFileAtomic from ../util/atomic-write for atomic saves
 * - TypeScript interfaces from ../types
 * - Synchronous file reads
 */

import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { writeFileAtomic } from "../util/atomic-write";
import type { LockedSkill } from "../types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface LockFileData {
  version: number;
  updated_at: string;
  skills: Record<string, LockedSkill>;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function hashContent(content: string): string {
  return createHash("sha256").update(content, "utf8").digest("hex");
}

function defaultLockFilePath(): string {
  return path.join(os.homedir(), ".claude", "auto-skill", "skills.lock.json");
}

function defaultData(): LockFileData {
  return {
    version: 0,
    updated_at: "",
    skills: {},
  };
}

// ---------------------------------------------------------------------------
// LockFile class
// ---------------------------------------------------------------------------

/**
 * Manages the skills lock file with integrity verification.
 *
 * Lock file path defaults to: ~/.claude/auto-skill/skills.lock.json
 */
export class LockFile {
  readonly path: string;
  private data: LockFileData;

  constructor(lockFilePath?: string) {
    this.path = lockFilePath ?? defaultLockFilePath();
    this.data = defaultData();
  }

  /**
   * Load the lock file from disk.
   *
   * @returns this (for chaining).
   */
  load(): this {
    try {
      if (fs.existsSync(this.path)) {
        const raw = fs.readFileSync(this.path, "utf-8");
        this.data = JSON.parse(raw) as LockFileData;
      } else {
        this.data = defaultData();
      }
    } catch {
      this.data = defaultData();
    }
    return this;
  }

  /**
   * Save the lock file atomically (temp file + rename).
   *
   * Increments the version counter on each save.
   */
  save(): void {
    this.data.version = (this.data.version ?? 0) + 1;
    this.data.updated_at = new Date().toISOString();
    writeFileAtomic(this.path, JSON.stringify(this.data, null, 2));
  }

  /**
   * Add or update a skill in the lock file.
   *
   * @param name - Skill name.
   * @param skillPath - Path to the SKILL.md file.
   * @param content - The SKILL.md file content (for hashing).
   * @param source - Source of the skill (default "auto").
   * @param metadata - Optional metadata.
   */
  addSkill(
    name: string,
    skillPath: string,
    content: string,
    source: string = "auto",
    metadata: Record<string, unknown> = {},
  ): void {
    this.data.skills[name] = {
      name,
      path: skillPath,
      contentHash: hashContent(content),
      source,
      lockedAt: new Date().toISOString(),
      metadata,
    };
  }

  /**
   * Remove a skill from the lock file.
   *
   * @returns true if removed, false if not found.
   */
  removeSkill(name: string): boolean {
    if (name in this.data.skills) {
      delete this.data.skills[name];
      return true;
    }
    return false;
  }

  /**
   * Get a locked skill by name.
   */
  getSkill(name: string): LockedSkill | undefined {
    return this.data.skills[name];
  }

  /**
   * List all locked skills.
   */
  listSkills(): LockedSkill[] {
    return Object.values(this.data.skills);
  }

  /**
   * Verify a skill's content matches its locked hash.
   *
   * @param name - Skill name.
   * @param content - Current SKILL.md content.
   * @returns true if content matches the locked hash, false if tampered or missing.
   */
  verifyIntegrity(name: string, content: string): boolean {
    const skill = this.getSkill(name);
    if (!skill) return false;
    return skill.contentHash === hashContent(content);
  }

  /**
   * Verify integrity of all locked skills.
   *
   * @param skillsDir - Root directory containing skill subdirectories.
   * @returns Map of skill name to integrity check result.
   */
  /** Alias for path, for convenience. */
  get filePath(): string {
    return this.path;
  }

  verifyAll(skillsDir?: string): Record<string, boolean> {
    const results: Record<string, boolean> = {};
    for (const locked of this.listSkills()) {
      const skillPath = locked.path;
      try {
        if (fs.existsSync(skillPath)) {
          const content = fs.readFileSync(skillPath, "utf-8");
          results[locked.name] = this.verifyIntegrity(locked.name, content);
        } else {
          results[locked.name] = false;
        }
      } catch {
        results[locked.name] = false;
      }
    }
    return results;
  }

  /**
   * Current version counter.
   */
  get version(): number {
    return this.data.version ?? 0;
  }

  /**
   * Number of skills in the lock file.
   */
  get skillCount(): number {
    return Object.keys(this.data.skills).length;
  }
}

/**
 * Factory function to create a LockFile instance.
 */
export function createLockFile(lockFilePath?: string): LockFile {
  return new LockFile(lockFilePath);
}
