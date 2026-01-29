/**
 * Provider Manager - Orchestrates multiple skill providers with priority ordering.
 *
 * Provides a unified search interface that queries all registered providers,
 * merges results, and handles graceful degradation when providers are unavailable.
 *
 * Ported from Python core/providers/manager.py.
 */

import type { SkillSearchResult } from "../../types";
import type { SkillProvider } from "./base";

/**
 * Create a provider manager that orchestrates multiple skill providers.
 *
 * Providers registered first have higher priority. When search results
 * from multiple providers match, higher-priority results appear first.
 */
export function createProviderManager(): {
  /** Register a provider. Earlier registrations have higher priority. */
  register(provider: SkillProvider): void;
  /** List of registered providers in priority order. */
  providers: SkillProvider[];
  /**
   * Search all available providers and merge results.
   *
   * Results are ordered by provider priority (first registered = highest).
   * Each provider contributes up to `limit` results, then the combined
   * list is deduplicated and truncated.
   *
   * @param query - Search keywords.
   * @param limit - Maximum total results to return (default 10).
   * @returns Merged and deduplicated list of SkillSearchResult objects.
   */
  searchAll(query: string, limit?: number): Promise<SkillSearchResult[]>;
  /**
   * Get skill details from the first provider that has it.
   *
   * @param skillId - The skill identifier.
   * @param sourceId - Optional provider sourceId to query specifically.
   * @returns SkillSearchResult if found, null otherwise.
   */
  getSkillDetails(
    skillId: string,
    sourceId?: string,
  ): Promise<SkillSearchResult | null>;
} {
  const registeredProviders: SkillProvider[] = [];

  /**
   * Check provider availability with error handling.
   */
  function isProviderAvailable(provider: SkillProvider): boolean {
    try {
      return provider.isAvailable();
    } catch (err) {
      console.warn(
        `[ProviderManager] Provider '${provider.name}' availability check failed: ${err}`,
      );
      return false;
    }
  }

  return {
    register(provider: SkillProvider): void {
      registeredProviders.push(provider);
    },

    get providers(): SkillProvider[] {
      return [...registeredProviders];
    },

    async searchAll(
      query: string,
      limit: number = 10,
    ): Promise<SkillSearchResult[]> {
      const allResults: SkillSearchResult[] = [];

      for (const provider of registeredProviders) {
        if (!isProviderAvailable(provider)) {
          continue;
        }

        try {
          const results = await provider.search(query, limit);
          allResults.push(...results);
        } catch (err) {
          console.warn(
            `[ProviderManager] Provider '${provider.name}' search failed: ${err}`,
          );
        }
      }

      // Deduplicate by (source, id) key
      const seen = new Set<string>();
      const unique: SkillSearchResult[] = [];

      for (const result of allResults) {
        const key = `${result.source}::${result.id}`;
        if (!seen.has(key)) {
          seen.add(key);
          unique.push(result);
        }
      }

      return unique.slice(0, limit);
    },

    async getSkillDetails(
      skillId: string,
      sourceId?: string,
    ): Promise<SkillSearchResult | null> {
      const providers = sourceId
        ? registeredProviders.filter((p) => p.sourceId === sourceId)
        : registeredProviders;

      for (const provider of providers) {
        if (!isProviderAvailable(provider)) {
          continue;
        }

        try {
          const result = await provider.getSkillDetails(skillId);
          if (result !== null) {
            return result;
          }
        } catch (err) {
          console.warn(
            `[ProviderManager] Provider '${provider.name}' getSkillDetails failed: ${err}`,
          );
        }
      }

      return null;
    },
  };
}
