/**
 * Well-Known Provider - RFC 8615 /.well-known/agent-skills.json discovery.
 *
 * Discovers skills from websites that publish a well-known agent-skills manifest.
 * See: https://www.rfc-editor.org/rfc/rfc8615
 *
 * Ported from Python core/providers/wellknown_provider.py.
 */

import https from "node:https";
import type { SkillSearchResult } from "../../types";
import type { SkillProvider } from "./base";

/** Default cache TTL in seconds (15 minutes). */
const DEFAULT_CACHE_TTL = 900;

/** Default HTTP timeout in seconds. */
const DEFAULT_TIMEOUT = 10;

/** Cached manifest entry. */
interface CacheEntry {
  timestamp: number;
  skills: Record<string, unknown>[];
}

/**
 * Fetch JSON from a URL using HTTPS.
 *
 * @param url - The URL to fetch.
 * @param timeout - Timeout in seconds.
 * @returns Parsed JSON response.
 */
function fetchJson(
  url: string,
  timeout: number,
): Promise<Record<string, unknown>> {
  return new Promise((resolve, reject) => {
    const req = https.get(
      url,
      {
        timeout: timeout * 1000,
        headers: { Accept: "application/json" },
      },
      (res) => {
        const chunks: Buffer[] = [];
        res.on("data", (chunk: Buffer) => chunks.push(chunk));
        res.on("end", () => {
          try {
            const body = Buffer.concat(chunks).toString("utf-8");
            const data = JSON.parse(body) as Record<string, unknown>;
            resolve(data);
          } catch (err) {
            reject(err);
          }
        });
        res.on("error", reject);
      },
    );
    req.on("timeout", () => {
      req.destroy();
      reject(new Error(`Request to ${url} timed out`));
    });
    req.on("error", reject);
  });
}

/**
 * Convert a skill manifest entry to a SkillSearchResult.
 */
function toSearchResult(
  skillData: Record<string, unknown>,
  domain: string,
): SkillSearchResult {
  const id =
    typeof skillData.id === "string"
      ? skillData.id
      : typeof skillData.name === "string"
        ? skillData.name
        : "";

  return {
    id,
    name: typeof skillData.name === "string" ? skillData.name : "",
    description:
      typeof skillData.description === "string" ? skillData.description : "",
    source: "wellknown",
    confidence: 0.5,
    author: typeof skillData.author === "string" ? skillData.author : domain,
    tags: Array.isArray(skillData.tags)
      ? (skillData.tags as string[])
      : [],
    installCount: 0,
    sourceUrl:
      typeof skillData.url === "string"
        ? skillData.url
        : `https://${domain}`,
    compatibleAgents: Array.isArray(skillData.compatible_agents)
      ? (skillData.compatible_agents as string[])
      : [],
    metadata: {
      domain,
      version: (skillData.version as string | undefined) ?? null,
    },
  };
}

/**
 * Create a well-known endpoint skill provider.
 *
 * Fetches and caches agent-skills.json manifests from configured domains
 * using the RFC 8615 /.well-known/ convention.
 *
 * @param domains - List of domains to query (e.g., ["example.com"]).
 * @param options - Optional configuration.
 * @param options.timeout - HTTP request timeout in seconds (default 10).
 * @param options.cacheTtl - Cache TTL in seconds (default 900, i.e. 15 min).
 * @returns A SkillProvider backed by well-known endpoints.
 */
export function createWellKnownProvider(
  domains: string[],
  options?: {
    timeout?: number;
    cacheTtl?: number;
  },
): SkillProvider {
  const timeout = options?.timeout ?? DEFAULT_TIMEOUT;
  const cacheTtl = options?.cacheTtl ?? DEFAULT_CACHE_TTL;
  const cache = new Map<string, CacheEntry>();

  /**
   * Fetch and cache skills from a domain's well-known endpoint.
   */
  async function fetchSkills(
    domain: string,
  ): Promise<Record<string, unknown>[]> {
    const now = Date.now() / 1000;

    // Check cache
    const cached = cache.get(domain);
    if (cached && now - cached.timestamp < cacheTtl) {
      return cached.skills;
    }

    // Fetch
    const url = `https://${domain}/.well-known/agent-skills.json`;
    try {
      const data = await fetchJson(url, timeout);

      // Validate manifest structure
      if (typeof data !== "object" || data === null || Array.isArray(data)) {
        console.warn(
          `[WellKnownProvider] Invalid manifest from ${domain}: not a JSON object`,
        );
        return [];
      }

      const skills = data.skills;
      if (!Array.isArray(skills)) {
        console.warn(
          `[WellKnownProvider] Invalid manifest from ${domain}: 'skills' is not a list`,
        );
        return [];
      }

      const skillList = skills as Record<string, unknown>[];

      // Cache result
      cache.set(domain, { timestamp: now, skills: skillList });
      return skillList;
    } catch (err) {
      console.debug?.(
        `[WellKnownProvider] Well-known fetch failed for ${domain}: ${err}`,
      );
      return [];
    }
  }

  return {
    name: "Well-Known Discovery",
    sourceId: "wellknown",

    async search(
      query: string,
      limit: number = 10,
    ): Promise<SkillSearchResult[]> {
      const allResults: SkillSearchResult[] = [];
      const queryLower = query.toLowerCase();

      for (const domain of domains) {
        const skills = await fetchSkills(domain);

        for (const skillData of skills) {
          const name =
            typeof skillData.name === "string" ? skillData.name : "";
          const description =
            typeof skillData.description === "string"
              ? skillData.description
              : "";
          const tags = Array.isArray(skillData.tags)
            ? (skillData.tags as string[]).join(" ")
            : "";

          const searchable =
            `${name} ${description} ${tags}`.toLowerCase();
          if (queryLower && !searchable.includes(queryLower)) {
            continue;
          }

          allResults.push(toSearchResult(skillData, domain));
        }
      }

      return allResults.slice(0, limit);
    },

    async getSkillDetails(
      skillId: string,
    ): Promise<SkillSearchResult | null> {
      for (const domain of domains) {
        const skills = await fetchSkills(domain);
        for (const skillData of skills) {
          if (skillData.id === skillId || skillData.name === skillId) {
            return toSearchResult(skillData, domain);
          }
        }
      }
      return null;
    },

    isAvailable(): boolean {
      return domains.length > 0;
    },
  };
}
