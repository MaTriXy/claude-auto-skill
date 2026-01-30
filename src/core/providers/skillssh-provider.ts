/**
 * Skills.sh Provider - Wraps the SkillsShClient as a SkillProvider.
 *
 * Adapts the SkillsShClient to the SkillProvider interface, converting
 * ExternalSkill objects to SkillSearchResult format.
 *
 * Ported from Python core/providers/skillssh_provider.py.
 */

import type { SkillSearchResult, ExternalSkill } from "../../types";
import type { SkillProvider } from "./base";
import { createSkillsShClient } from "../skillssh-client";

/**
 * Convert an ExternalSkill to a SkillSearchResult.
 */
function toSearchResult(ext: ExternalSkill): SkillSearchResult {
  return {
    id: ext.id,
    name: ext.name,
    description: ext.description,
    source: "skillssh",
    confidence: 0.5,
    author: ext.author,
    tags: ext.tags,
    installCount: ext.installCount,
    sourceUrl: ext.sourceUrl,
    compatibleAgents: ext.compatibleAgents,
    metadata: {
      createdAt: ext.createdAt ?? null,
      updatedAt: ext.updatedAt ?? null,
    },
  };
}

/**
 * Create a Skills.sh skill provider.
 *
 * Delegates to the SkillsShClient for API access and converts results
 * to the SkillSearchResult format.
 *
 * @param client - Optional SkillsShClient instance. If omitted, a default
 *   client is created.
 * @returns A SkillProvider backed by Skills.sh.
 */
export function createSkillsShProvider(
  client?: ReturnType<typeof createSkillsShClient>,
): SkillProvider {
  const skillsClient = client ?? createSkillsShClient();

  return {
    name: "Skills.sh",
    sourceId: "skillssh",

    async search(
      query: string,
      limit: number = 10,
    ): Promise<SkillSearchResult[]> {
      const externalSkills = await skillsClient.search(query, limit);
      return externalSkills.map(toSearchResult);
    },

    async getSkillDetails(
      skillId: string,
    ): Promise<SkillSearchResult | null> {
      const ext = await skillsClient.getSkillDetails(skillId);
      if (ext === null) {
        return null;
      }
      return toSearchResult(ext);
    },

    isAvailable(): boolean {
      // Skills.sh is assumed available; actual availability checked on request
      return true;
    },
  };
}
