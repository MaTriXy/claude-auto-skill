/**
 * Base provider interface for skill discovery sources.
 *
 * All skill providers must implement the SkillProvider interface.
 * This enables pluggable discovery from different sources (Skills.sh,
 * local filesystem, well-known endpoints, etc.).
 *
 * Ported from Python core/providers/base.py.
 */

import type { SkillSearchResult } from "../../types";

export type { SkillSearchResult };

/** Interface for skill discovery providers. */
export interface SkillProvider {
  /** Human-readable name of this provider (e.g., 'Skills.sh'). */
  readonly name: string;

  /** Short identifier used in results (e.g., 'skillssh', 'local'). */
  readonly sourceId: string;

  /**
   * Search for skills matching a query.
   *
   * @param query - Search keywords.
   * @param limit - Maximum number of results (default 10).
   * @returns List of matching SkillSearchResult objects.
   */
  search(query: string, limit?: number): Promise<SkillSearchResult[]>;

  /**
   * Get detailed information about a specific skill.
   *
   * @param skillId - The skill identifier.
   * @returns SkillSearchResult with full details, or null if not found.
   */
  getSkillDetails(skillId: string): Promise<SkillSearchResult | null>;

  /**
   * Check if this provider is currently available.
   *
   * @returns True if the provider can serve requests, false otherwise.
   */
  isAvailable(): boolean;
}
