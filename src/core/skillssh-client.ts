/**
 * Skills.sh API Client - Integrates Vercel's external skill discovery.
 *
 * Provides access to the skills.sh community skill registry:
 * - Search for skills by query
 * - Get trending skills
 * - Fetch skill details
 * - Get skills by tag
 *
 * API Endpoint: https://skills.sh
 *
 * Ported from Python core/skillssh_client.py.
 */

import https from "node:https";
import type { ExternalSkill } from "../types";

const BASE_URL = "https://skills.sh";

/** Default HTTP timeout in milliseconds. */
const DEFAULT_TIMEOUT_MS = 10_000;

/**
 * Fetch JSON from a URL using HTTPS.
 *
 * @param url - The URL to fetch.
 * @param timeoutMs - Timeout in milliseconds.
 * @returns Parsed JSON response.
 */
function fetchJson(
  url: string,
  timeoutMs: number,
): Promise<Record<string, unknown>> {
  return new Promise((resolve, reject) => {
    const req = https.get(
      url,
      {
        timeout: timeoutMs,
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
 * Parse an API response item into an ExternalSkill.
 *
 * @param item - Raw skill data from the API.
 * @returns Parsed ExternalSkill object.
 */
function parseSkill(item: Record<string, unknown>): ExternalSkill {
  return {
    id: typeof item.id === "string" ? item.id : "",
    name: typeof item.name === "string" ? item.name : "",
    description: typeof item.description === "string" ? item.description : "",
    author: typeof item.author === "string" ? item.author : "unknown",
    installCount:
      typeof item.installCount === "number" ? item.installCount : 0,
    tags: Array.isArray(item.tags) ? (item.tags as string[]) : [],
    sourceUrl: typeof item.sourceUrl === "string" ? item.sourceUrl : "",
    compatibleAgents: Array.isArray(item.compatibleAgents)
      ? (item.compatibleAgents as string[])
      : [],
    createdAt:
      typeof item.createdAt === "string" ? item.createdAt : null,
    updatedAt:
      typeof item.updatedAt === "string" ? item.updatedAt : null,
  };
}

/**
 * Create a Skills.sh API client.
 *
 * All methods wrap HTTP calls in try-catch, returning empty arrays or null on
 * failure rather than throwing.
 *
 * @param timeout - Request timeout in milliseconds (default 10000).
 * @returns Client object with search, trending, details, and availability methods.
 */
export function createSkillsShClient(timeout?: number): {
  /**
   * Search for skills by query.
   *
   * @param query - Search query (keywords, tags, etc.).
   * @param limit - Maximum number of results (default 10).
   * @returns List of matching ExternalSkill objects.
   */
  search(query: string, limit?: number): Promise<ExternalSkill[]>;

  /**
   * Get trending skills.
   *
   * @param limit - Maximum number of results (default 20).
   * @returns List of trending ExternalSkill objects.
   */
  getTrending(limit?: number): Promise<ExternalSkill[]>;

  /**
   * Get detailed information about a specific skill.
   *
   * @param skillId - Skill identifier.
   * @returns ExternalSkill with full details, or null if not found.
   */
  getSkillDetails(skillId: string): Promise<ExternalSkill | null>;

  /**
   * Get skills by tag.
   *
   * @param tag - Tag to filter by (e.g., "payment", "authentication").
   * @param limit - Maximum number of results (default 10).
   * @returns List of matching ExternalSkill objects.
   */
  getSkillsByTag(tag: string, limit?: number): Promise<ExternalSkill[]>;

  /**
   * Check if skills.sh API is available.
   *
   * @returns True if the API is accessible, false otherwise.
   */
  isAvailable(): Promise<boolean>;
} {
  const timeoutMs = timeout ?? DEFAULT_TIMEOUT_MS;

  return {
    async search(
      query: string,
      limit: number = 10,
    ): Promise<ExternalSkill[]> {
      try {
        const params = new URLSearchParams({
          q: query,
          limit: String(limit),
        });
        const url = `${BASE_URL}/api/skills/search?${params}`;
        const data = await fetchJson(url, timeoutMs);
        const items = Array.isArray(data.skills)
          ? (data.skills as Record<string, unknown>[])
          : [];
        return items.map(parseSkill);
      } catch (err) {
        console.warn(`[Skills.sh] Search failed: ${err}`);
        return [];
      }
    },

    async getTrending(limit: number = 20): Promise<ExternalSkill[]> {
      try {
        const url = `${BASE_URL}/api/skills/trending?limit=${limit}`;
        const data = await fetchJson(url, timeoutMs);
        const items = Array.isArray(data.skills)
          ? (data.skills as Record<string, unknown>[])
          : [];
        return items.map(parseSkill);
      } catch (err) {
        console.warn(`[Skills.sh] Get trending failed: ${err}`);
        return [];
      }
    },

    async getSkillDetails(
      skillId: string,
    ): Promise<ExternalSkill | null> {
      try {
        const url = `${BASE_URL}/api/skills/${encodeURIComponent(skillId)}`;
        const data = await fetchJson(url, timeoutMs);
        return parseSkill(data);
      } catch (err) {
        console.warn(`[Skills.sh] Get details failed: ${err}`);
        return null;
      }
    },

    async getSkillsByTag(
      tag: string,
      limit: number = 10,
    ): Promise<ExternalSkill[]> {
      try {
        const params = new URLSearchParams({
          tag,
          limit: String(limit),
        });
        const url = `${BASE_URL}/api/skills/by-tag?${params}`;
        const data = await fetchJson(url, timeoutMs);
        const items = Array.isArray(data.skills)
          ? (data.skills as Record<string, unknown>[])
          : [];
        return items.map(parseSkill);
      } catch (err) {
        console.warn(`[Skills.sh] Get by tag failed: ${err}`);
        return [];
      }
    },

    async isAvailable(): Promise<boolean> {
      try {
        const url = `${BASE_URL}/api/health`;
        await fetchJson(url, 5000);
        return true;
      } catch {
        return false;
      }
    },
  };
}
