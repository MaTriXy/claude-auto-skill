/**
 * Skill Adoption Tracker — Tracks usage of external skills and confidence evolution.
 *
 * Tracks skill adoption lifecycle:
 * 1. External skill discovered (50% confidence)
 * 2. Usage tracked (confidence increases with success rate)
 * 3. Graduation to local skill (85%+ confidence, 5+ uses, 80%+ success)
 *
 * Confidence Evolution:
 * - External: Start at 50%
 * - Proven: Reach 75% (3+ uses, 70%+ success)
 * - Local: Graduate at 85% (5+ uses, 80%+ success)
 *
 * Ported from Python core/skill_tracker.py.
 * Key changes:
 * - SQLite-backed via openDatabase()
 * - Synchronous API (better-sqlite3 is sync)
 * - TypeScript interfaces from ../types
 */

import { openDatabase, type Database } from "./db";
import { getAutoSkillDir } from "../util/fs";
import path from "node:path";
import type { SkillAdoption, SkillTrackerStats } from "../types";

// ---------------------------------------------------------------------------
// Confidence map
// ---------------------------------------------------------------------------

const INITIAL_CONFIDENCE: Record<string, number> = {
  external: 0.5,
  "mental-hint": 0.6,
  local: 0.8,
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getInitialConfidence(source: string): number {
  return INITIAL_CONFIDENCE[source] ?? 0.5;
}

/**
 * Calculate confidence based on usage and success.
 *
 * Confidence evolution:
 * - Starts at initial confidence
 * - Increases with successful usage
 * - Capped at 0.95 for external, 1.0 for local
 */
function calculateConfidence(
  initial: number,
  source: string,
  usageCount: number,
  successRate: number,
): number {
  // Usage factor: more uses = higher confidence (cap at 10 uses)
  const usageFactor = Math.min(usageCount / 10.0, 1.0);

  // Weighted combination: 70% success rate, 30% usage count
  const weightedConfidence = successRate * 0.7 + usageFactor * 0.3;

  // Blend with initial confidence (30% initial, 70% weighted)
  const newConfidence = initial * 0.3 + weightedConfidence * 0.7;

  // Cap based on source
  const maxConfidence = source === "external" ? 0.95 : 1.0;

  return Math.min(newConfidence, maxConfidence);
}

/**
 * Convert a DB row to a SkillAdoption.
 */
function rowToAdoption(row: Record<string, unknown>): SkillAdoption {
  return {
    skillId: row.skill_id as string,
    skillName: row.skill_name as string,
    source: row.source as string,
    initialConfidence: row.initial_confidence as number,
    currentConfidence: row.current_confidence as number,
    usageCount: (row.usage_count as number) ?? 0,
    successCount: (row.success_count as number) ?? 0,
    failureCount: (row.failure_count as number) ?? 0,
    firstUsed: row.first_used as string,
    lastUsed: row.last_used as string,
    graduatedToLocal: Boolean(row.graduated_to_local),
  };
}

// ---------------------------------------------------------------------------
// SkillTracker class
// ---------------------------------------------------------------------------

/**
 * Tracks skill adoption and evolution.
 *
 * Uses SQLite to persist skill usage data and calculate confidence scores
 * based on usage patterns and success rates.
 */
export class SkillTracker {
  private db: Database;

  /**
   * Create a SkillTracker.
   *
   * @param dbPath - Path to SQLite database (default: ~/.claude/auto-skill/skills_tracking.db).
   */
  constructor(dbPath?: string) {
    const resolvedPath =
      dbPath ?? path.join(getAutoSkillDir(), "skills_tracking.db");
    this.db = openDatabase(resolvedPath);
    this.initSchema();
  }

  private initSchema(): void {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS skill_adoptions (
        skill_id TEXT PRIMARY KEY,
        skill_name TEXT NOT NULL,
        source TEXT NOT NULL,
        initial_confidence REAL NOT NULL,
        current_confidence REAL NOT NULL,
        usage_count INTEGER DEFAULT 0,
        success_count INTEGER DEFAULT 0,
        failure_count INTEGER DEFAULT 0,
        first_used TEXT NOT NULL,
        last_used TEXT NOT NULL,
        graduated_to_local INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
      )
    `);
    this.db.exec(
      "CREATE INDEX IF NOT EXISTS idx_confidence ON skill_adoptions(current_confidence)",
    );
    this.db.exec(
      "CREATE INDEX IF NOT EXISTS idx_source ON skill_adoptions(source)",
    );
  }

  /**
   * Record a skill usage event.
   *
   * Updates confidence score based on usage patterns and success rate.
   */
  trackUsage(
    skillId: string,
    skillName: string,
    source: string,
    success: boolean,
  ): void {
    const now = new Date().toISOString();

    const existing = this.db
      .prepare("SELECT * FROM skill_adoptions WHERE skill_id = ?")
      .get(skillId) as Record<string, unknown> | undefined;

    if (existing) {
      const usageCount = ((existing.usage_count as number) ?? 0) + 1;
      const successCount =
        ((existing.success_count as number) ?? 0) + (success ? 1 : 0);
      const failureCount =
        ((existing.failure_count as number) ?? 0) + (success ? 0 : 1);

      const successRate = usageCount > 0 ? successCount / usageCount : 0;
      const currentConfidence = calculateConfidence(
        existing.initial_confidence as number,
        existing.source as string,
        usageCount,
        successRate,
      );

      this.db
        .prepare(
          `UPDATE skill_adoptions
           SET usage_count = ?,
               success_count = ?,
               failure_count = ?,
               current_confidence = ?,
               last_used = ?,
               updated_at = ?
           WHERE skill_id = ?`,
        )
        .run(
          usageCount,
          successCount,
          failureCount,
          currentConfidence,
          now,
          now,
          skillId,
        );
    } else {
      const initialConfidence = getInitialConfidence(source);

      this.db
        .prepare(
          `INSERT INTO skill_adoptions
             (skill_id, skill_name, source, initial_confidence, current_confidence,
              usage_count, success_count, failure_count, first_used, last_used)
           VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?)`,
        )
        .run(
          skillId,
          skillName,
          source,
          initialConfidence,
          initialConfidence,
          success ? 1 : 0,
          success ? 0 : 1,
          now,
          now,
        );
    }
  }

  /**
   * Get adoption details for a skill.
   */
  getAdoption(skillId: string): SkillAdoption | undefined {
    const row = this.db
      .prepare("SELECT * FROM skill_adoptions WHERE skill_id = ?")
      .get(skillId) as Record<string, unknown> | undefined;

    if (!row) return undefined;
    return rowToAdoption(row);
  }

  /**
   * Get all skill adoptions above minimum confidence.
   */
  listAdoptions(minConfidence: number = 0.0): SkillAdoption[] {
    const rows = this.db
      .prepare(
        `SELECT * FROM skill_adoptions
         WHERE current_confidence >= ?
         ORDER BY current_confidence DESC, usage_count DESC`,
      )
      .all(minConfidence) as Record<string, unknown>[];

    return rows.map(rowToAdoption);
  }

  /**
   * Check if a skill should be graduated to local.
   *
   * Graduation criteria:
   * - Confidence >= 0.85
   * - Used at least 5 times
   * - Success rate >= 0.8
   * - Not already graduated
   * - Must be an external skill
   */
  shouldGraduate(skillId: string): boolean {
    const adoption = this.getAdoption(skillId);
    if (!adoption || adoption.graduatedToLocal) return false;
    if (adoption.source !== "external") return false;

    const successRate =
      adoption.usageCount > 0
        ? adoption.successCount / adoption.usageCount
        : 0;

    return (
      adoption.currentConfidence >= 0.85 &&
      adoption.usageCount >= 5 &&
      successRate >= 0.8
    );
  }

  /**
   * Mark a skill as graduated to local.
   */
  markGraduated(skillId: string): void {
    const now = new Date().toISOString();
    this.db
      .prepare(
        `UPDATE skill_adoptions
         SET graduated_to_local = 1,
             source = 'local',
             current_confidence = 0.85,
             updated_at = ?
         WHERE skill_id = ?`,
      )
      .run(now, skillId);
  }

  /**
   * Get all skills that are candidates for graduation.
   */
  getGraduationCandidates(): SkillAdoption[] {
    const adoptions = this.listAdoptions(0.8);
    return adoptions.filter((a) => this.shouldGraduate(a.skillId));
  }

  /**
   * Get tracker statistics.
   */
  getStats(): SkillTrackerStats {
    const totalSkills = (
      this.db
        .prepare("SELECT COUNT(*) AS cnt FROM skill_adoptions")
        .get() as { cnt: number }
    ).cnt;

    const avgRow = this.db
      .prepare(
        "SELECT AVG(current_confidence) AS avg FROM skill_adoptions",
      )
      .get() as { avg: number | null };
    const avgConfidence = avgRow?.avg ?? 0;

    const graduatedCount = (
      this.db
        .prepare(
          "SELECT COUNT(*) AS cnt FROM skill_adoptions WHERE graduated_to_local = 1",
        )
        .get() as { cnt: number }
    ).cnt;

    const totalUsage = (
      this.db
        .prepare(
          "SELECT COALESCE(SUM(usage_count), 0) AS total FROM skill_adoptions",
        )
        .get() as { total: number }
    ).total;

    const sourceRows = this.db
      .prepare(
        `SELECT source, COUNT(*) AS cnt
         FROM skill_adoptions
         GROUP BY source`,
      )
      .all() as Array<{ source: string; cnt: number }>;

    const bySource: Record<string, number> = {};
    for (const row of sourceRows) {
      bySource[row.source] = row.cnt;
    }

    return {
      total_skills: totalSkills,
      avg_confidence: avgConfidence,
      graduated_count: graduatedCount,
      total_usage: totalUsage,
      by_source: bySource,
    };
  }

  /**
   * Close the database connection.
   */
  close(): void {
    this.db.close();
  }
}

/**
 * Factory function to create a SkillTracker instance.
 */
export function createSkillTracker(dbPath?: string): SkillTracker {
  return new SkillTracker(dbPath);
}
