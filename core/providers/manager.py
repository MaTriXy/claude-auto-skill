"""
Provider Manager - Orchestrates multiple skill providers with priority ordering.

Provides a unified search interface that queries all registered providers,
merges results, and handles graceful degradation when providers are unavailable.
"""

import logging
from typing import Optional

from .base import SkillProvider, SkillSearchResult

logger = logging.getLogger(__name__)


class ProviderManager:
    """Manages multiple skill providers with priority-based ordering.

    Providers registered first have higher priority. When search results
    from multiple providers match, higher-priority results appear first.
    """

    def __init__(self):
        self._providers: list[SkillProvider] = []

    def register(self, provider: SkillProvider):
        """Register a provider. Earlier registrations have higher priority.

        Args:
            provider: A SkillProvider implementation.
        """
        self._providers.append(provider)

    @property
    def providers(self) -> list[SkillProvider]:
        """List of registered providers in priority order."""
        return list(self._providers)

    def search_all(self, query: str, limit: int = 10) -> list[SkillSearchResult]:
        """Search all available providers and merge results.

        Results are ordered by provider priority (first registered = highest).
        Each provider contributes up to `limit` results, then the combined
        list is deduplicated and truncated.

        Args:
            query: Search keywords.
            limit: Maximum total results to return.

        Returns:
            Merged and deduplicated list of SkillSearchResult objects.
        """
        all_results: list[SkillSearchResult] = []

        for provider in self._providers:
            if not self._is_provider_available(provider):
                continue

            try:
                results = provider.search(query, limit=limit)
                all_results.extend(results)
            except Exception as e:
                logger.warning(
                    f"Provider '{provider.name}' search failed: {e}"
                )

        # Deduplicate by (source_id, skill_id)
        seen = set()
        unique = []
        for result in all_results:
            key = (result.source, result.id)
            if key not in seen:
                seen.add(key)
                unique.append(result)

        return unique[:limit]

    def get_skill_details(
        self, skill_id: str, source_id: Optional[str] = None
    ) -> Optional[SkillSearchResult]:
        """Get skill details from the first provider that has it.

        Args:
            skill_id: The skill identifier.
            source_id: Optional provider source_id to query specifically.

        Returns:
            SkillSearchResult if found, None otherwise.
        """
        providers = self._providers
        if source_id:
            providers = [p for p in providers if p.source_id == source_id]

        for provider in providers:
            if not self._is_provider_available(provider):
                continue
            try:
                result = provider.get_skill_details(skill_id)
                if result is not None:
                    return result
            except Exception as e:
                logger.warning(
                    f"Provider '{provider.name}' get_skill_details failed: {e}"
                )

        return None

    def _is_provider_available(self, provider: SkillProvider) -> bool:
        """Check provider availability with error handling."""
        try:
            return provider.is_available()
        except Exception as e:
            logger.warning(f"Provider '{provider.name}' availability check failed: {e}")
            return False
