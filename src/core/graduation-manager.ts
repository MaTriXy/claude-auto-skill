/**
 * Graduation Manager - Automatic skill graduation from external to local.
 *
 * Handles:
 * 1. Detection of graduation candidates (external skills with high confidence)
 * 2. Generation of local skills from external sources
 * 3. Metadata updates and tracking
 * 4. Graduation history logging
 *
 * Ported from Python core/graduation_manager.py (~475 lines).
 */

import fs from "node:fs";
import path from "node:path";

import { sanitizeName } from "./path-security";
import { writeFileAtomic } from "../util/atomic-write";
import type { GraduationCandidate } from "../types";

// ---------------------------------------------------------------------------
// Graduation thresholds
// ---------------------------------------------------------------------------

/** Minimum confidence score required for graduation. */
const MIN_CONFIDENCE = 0.85;

/** Minimum number of uses required for graduation. */
const MIN_USAGE_COUNT = 5;

/** Minimum success rate required for graduation. */
const MIN_SUCCESS_RATE = 0.80;

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/**
 * Check if a graduation candidate meets all criteria.
 *
 * @param candidate - The candidate to evaluate.
 * @returns True if the candidate meets confidence, usage, and success thresholds.
 */
function meetsCriteria(candidate: GraduationCandidate): boolean {
  return (
    candidate.currentConfidence >= MIN_CONFIDENCE &&
    candidate.usageCount >= MIN_USAGE_COUNT &&
    candidate.successRate >= MIN_SUCCESS_RATE
  );
}

/**
 * Build the full SKILL.md content for a graduated skill.
 *
 * Produces YAML frontmatter with graduation metadata followed by a
 * descriptive body documenting the graduation reason, original metadata,
 * and usage guidance.
 *
 * @param candidate - The graduation candidate.
 * @returns Formatted SKILL.md content string.
 */
function buildGraduatedSkillContent(candidate: GraduationCandidate): string {
  const metadata = (candidate.metadata ?? {}) as Record<string, unknown>;
  const now = new Date().toISOString();

  // Build frontmatter
  let frontmatter = `---
name: ${candidate.skillName}
confidence: 0.80

# Source
source: local
derived-from: ${candidate.source}
graduated-at: ${now}

# Adoption stats
usage-count: ${candidate.usageCount}
success-rate: ${candidate.successRate.toFixed(2)}
first-used: ${candidate.firstUsed || "unknown"}
last-used: ${candidate.lastUsed || "unknown"}

# Vercel compatibility
compatible-agents: [claude-code, opencode, codex]
tags: ${JSON.stringify((metadata.tags as string[]) ?? [])}
`;

  if (metadata.mental_context) {
    const mental = metadata.mental_context as Record<string, unknown>;
    if (mental.domains) {
      const domains = (mental.domains as Array<Record<string, unknown>>).map(
        (d) => String(d.name),
      );
      frontmatter += `\n# Mental context\ndomains: ${JSON.stringify(domains)}\n`;
    }
  }

  frontmatter += "---\n\n";

  // Build body
  const description = metadata.description
    ? String(metadata.description)
    : "No description available";

  let body = `# ${candidate.skillName}

**Graduated from**: ${candidate.source}
**Status**: Local (promoted from external)

## Description

${description}

## Why This Skill Was Graduated

This skill was automatically graduated from external (${candidate.source}) to local based on proven adoption:

- **Usage**: ${candidate.usageCount} times
- **Success Rate**: ${Math.round(candidate.successRate * 100)}%
- **Final Confidence**: 80% (local)

The skill has been validated through real-world usage and promoted to a trusted local skill.

## Original Metadata

`;

  if (metadata.author) {
    body += `- **Original Author**: ${String(metadata.author)}\n`;
  }
  if (metadata.installs) {
    body += `- **Community Installs**: ${String(metadata.installs)}\n`;
  }
  if (metadata.url) {
    body += `- **Original Source**: ${String(metadata.url)}\n`;
  }

  body += "\n## Usage\n\n";
  body += metadata.usage
    ? String(metadata.usage)
    : "Use this skill by referencing it in your workflow.";

  body += "\n\n## Success Indicators\n\n";
  body += "- Task completed successfully\n";
  body += "- No errors or warnings\n";
  body += "- Code quality maintained\n";

  return frontmatter + body;
}

// ---------------------------------------------------------------------------
// Public factory
// ---------------------------------------------------------------------------

/**
 * Create a graduation manager instance.
 *
 * Manages the lifecycle of skill graduation: detecting candidates,
 * generating local skill files, and maintaining a graduation log.
 *
 * @param trackerDbPath - Path to the skill tracker SQLite database (reserved for future use).
 * @param skillsOutputDir - Directory to save graduated skill files.
 * @returns An object with graduation detection, execution, history, and statistics methods.
 */
export function createGraduationManager(
  trackerDbPath: string,
  skillsOutputDir: string,
): {
  detectCandidates(
    stats: Record<string, Record<string, unknown>>,
  ): GraduationCandidate[];

  graduateSkill(candidate: GraduationCandidate): string | null;

  autoGraduateAll(
    stats: Record<string, Record<string, unknown>>,
    maxCount?: number,
  ): string[];

  getGraduationHistory(): Array<Record<string, unknown>>;

  statsSummary(
    stats: Record<string, Record<string, unknown>>,
  ): Record<string, unknown>;
} {
  const skillsDir = path.resolve(skillsOutputDir);
  const graduationLogPath = path.join(skillsDir, "graduation_log.json");

  // Ensure the output directory exists
  fs.mkdirSync(skillsDir, { recursive: true });

  // ---------------------------------------------------------------
  // Graduation log persistence
  // ---------------------------------------------------------------

  /** Load the graduation history from disk. */
  function loadGraduationLog(): Array<Record<string, unknown>> {
    try {
      if (fs.existsSync(graduationLogPath)) {
        const raw = fs.readFileSync(graduationLogPath, "utf-8");
        return JSON.parse(raw) as Array<Record<string, unknown>>;
      }
    } catch {
      // Corrupted log — start fresh
    }
    return [];
  }

  /** Persist the graduation history to disk. */
  function saveGraduationLog(log: Array<Record<string, unknown>>): void {
    writeFileAtomic(graduationLogPath, JSON.stringify(log, null, 2));
  }

  /** Check if a skill has already been graduated. */
  function isGraduated(
    skillName: string,
    log: Array<Record<string, unknown>>,
  ): boolean {
    return log.some((entry) => entry.skill_name === skillName);
  }

  // ---------------------------------------------------------------
  // detectCandidates
  // ---------------------------------------------------------------

  /**
   * Detect skills eligible for graduation from aggregated stats.
   *
   * Filters for external or mental-hint skills that meet confidence,
   * usage, and success-rate thresholds. Results are sorted by
   * descending confidence.
   *
   * @param stats - Aggregated per-skill statistics keyed by skill name.
   * @returns Graduation candidates sorted by confidence (highest first).
   */
  function detectCandidates(
    stats: Record<string, Record<string, unknown>>,
  ): GraduationCandidate[] {
    const log = loadGraduationLog();
    const candidates: GraduationCandidate[] = [];

    for (const [skillName, skillStats] of Object.entries(stats)) {
      // Skip already graduated
      if (isGraduated(skillName, log)) {
        continue;
      }

      // Skip local skills
      const source = String(skillStats.source ?? "external");
      if (source === "local") {
        continue;
      }

      // Only graduate external or mental-hint skills
      if (source !== "external" && source !== "mental-hint") {
        continue;
      }

      const usageCount = Number(skillStats.usage_count ?? 0);
      const successCount = Number(skillStats.success_count ?? 0);
      const successRate = usageCount > 0 ? successCount / usageCount : 0;

      const candidate: GraduationCandidate = {
        skillName,
        currentConfidence: Number(skillStats.confidence ?? 0.5),
        usageCount,
        successCount,
        successRate,
        firstUsed: skillStats.first_used ? String(skillStats.first_used) : "",
        lastUsed: skillStats.last_used ? String(skillStats.last_used) : "",
        source,
        metadata: (skillStats.metadata as Record<string, unknown>) ?? null,
      };

      if (meetsCriteria(candidate)) {
        candidates.push(candidate);
      }
    }

    // Sort by confidence descending
    candidates.sort((a, b) => b.currentConfidence - a.currentConfidence);
    return candidates;
  }

  // ---------------------------------------------------------------
  // graduateSkill
  // ---------------------------------------------------------------

  /**
   * Graduate a single skill candidate to a local SKILL.md file.
   *
   * Writes the graduated skill file and appends to the graduation log.
   *
   * @param candidate - The graduation candidate to promote.
   * @returns Absolute path to the generated skill file, or null on failure.
   */
  function graduateSkill(candidate: GraduationCandidate): string | null {
    try {
      const safeName = sanitizeName(candidate.skillName);
      const skillContent = buildGraduatedSkillContent(candidate);
      const skillPath = path.join(skillsDir, `${safeName}.md`);

      // Ensure parent directory exists
      fs.mkdirSync(path.dirname(skillPath), { recursive: true });
      writeFileAtomic(skillPath, skillContent);

      // Log graduation
      const log = loadGraduationLog();
      log.push({
        skill_name: candidate.skillName,
        graduated_at: new Date().toISOString(),
        graduated_from: candidate.source,
        usage_count: candidate.usageCount,
        success_rate: candidate.successRate,
        final_confidence: 0.80,
        skill_path: skillPath,
      });
      saveGraduationLog(log);

      return skillPath;
    } catch {
      return null;
    }
  }

  // ---------------------------------------------------------------
  // autoGraduateAll
  // ---------------------------------------------------------------

  /**
   * Automatically graduate the top candidates without user prompting.
   *
   * @param stats - Aggregated per-skill statistics.
   * @param maxCount - Maximum number of skills to graduate (default 5).
   * @returns Array of paths to graduated skill files.
   */
  function autoGraduateAll(
    stats: Record<string, Record<string, unknown>>,
    maxCount = 5,
  ): string[] {
    const candidates = detectCandidates(stats).slice(0, maxCount);
    if (candidates.length === 0) {
      return [];
    }

    const graduated: string[] = [];
    for (const candidate of candidates) {
      const skillPath = graduateSkill(candidate);
      if (skillPath) {
        graduated.push(skillPath);
      }
    }

    return graduated;
  }

  // ---------------------------------------------------------------
  // getGraduationHistory
  // ---------------------------------------------------------------

  /**
   * Retrieve the full graduation history.
   *
   * @returns A copy of the graduation log entries.
   */
  function getGraduationHistory(): Array<Record<string, unknown>> {
    return [...loadGraduationLog()];
  }

  // ---------------------------------------------------------------
  // statsSummary
  // ---------------------------------------------------------------

  /**
   * Get a summary of graduation statistics.
   *
   * @param stats - Aggregated per-skill statistics (used to count pending candidates).
   * @returns Object with total graduated, pending candidates, graduation rate, and recent entries.
   */
  function statsSummary(
    stats: Record<string, Record<string, unknown>>,
  ): Record<string, unknown> {
    const log = loadGraduationLog();
    const totalGraduated = log.length;
    const candidates = detectCandidates(stats);
    const total = totalGraduated + candidates.length;

    return {
      total_graduated: totalGraduated,
      pending_candidates: candidates.length,
      graduation_rate:
        total > 0 ? `${((totalGraduated / total) * 100).toFixed(1)}%` : "0%",
      recent_graduations: log.slice(-5),
    };
  }

  return {
    detectCandidates,
    graduateSkill,
    autoGraduateAll,
    getGraduationHistory,
    statsSummary,
  };
}
