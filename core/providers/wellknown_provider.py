"""
Well-Known Provider - RFC 8615 /.well-known/agent-skills.json discovery.

Discovers skills from websites that publish a well-known agent-skills manifest.
See: https://www.rfc-editor.org/rfc/rfc8615
"""

import json
import logging
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

from .base import SkillProvider, SkillSearchResult

logger = logging.getLogger(__name__)

# Cache TTL in seconds (15 minutes)
_CACHE_TTL = 900


class WellKnownProvider:
    """SkillProvider that discovers skills from /.well-known/agent-skills.json endpoints.

    Websites can publish an agent-skills.json manifest at their well-known URI
    to advertise available skills. This provider fetches and caches those manifests.
    """

    def __init__(
        self,
        domains: Optional[list[str]] = None,
        timeout: int = 10,
        cache_ttl: int = _CACHE_TTL,
    ):
        """Initialize the well-known provider.

        Args:
            domains: List of domains to query (e.g., ["example.com", "skills.dev"]).
            timeout: HTTP request timeout in seconds.
            cache_ttl: Cache TTL in seconds.
        """
        self._domains = domains or []
        self._timeout = timeout
        self._cache_ttl = cache_ttl
        self._cache: dict[str, tuple[float, list[dict]]] = {}  # domain -> (timestamp, skills)

    @property
    def name(self) -> str:
        return "Well-Known Discovery"

    @property
    def source_id(self) -> str:
        return "wellknown"

    def search(self, query: str, limit: int = 10) -> list[SkillSearchResult]:
        """Search across all configured domains for matching skills."""
        all_results = []
        query_lower = query.lower()

        for domain in self._domains:
            skills = self._fetch_skills(domain)
            for skill_data in skills:
                searchable = (
                    f"{skill_data.get('name', '')} "
                    f"{skill_data.get('description', '')} "
                    f"{' '.join(skill_data.get('tags', []))}"
                ).lower()

                if query_lower and query_lower not in searchable:
                    continue

                result = self._to_search_result(skill_data, domain)
                all_results.append(result)

        return all_results[:limit]

    def get_skill_details(self, skill_id: str) -> Optional[SkillSearchResult]:
        """Get skill details by ID across all domains."""
        for domain in self._domains:
            skills = self._fetch_skills(domain)
            for skill_data in skills:
                if skill_data.get("id") == skill_id or skill_data.get("name") == skill_id:
                    return self._to_search_result(skill_data, domain)
        return None

    def is_available(self) -> bool:
        """Check if at least one domain is configured."""
        return len(self._domains) > 0

    def _fetch_skills(self, domain: str) -> list[dict]:
        """Fetch and cache skills from a domain's well-known endpoint.

        Args:
            domain: The domain to fetch from.

        Returns:
            List of skill data dicts, or empty list on failure.
        """
        now = time.time()

        # Check cache
        if domain in self._cache:
            cached_time, cached_skills = self._cache[domain]
            if now - cached_time < self._cache_ttl:
                return cached_skills

        # Fetch
        url = f"https://{domain}/.well-known/agent-skills.json"
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=self._timeout) as response:
                data = json.loads(response.read().decode())

            # Validate manifest structure
            if not isinstance(data, dict):
                logger.warning(f"Invalid manifest from {domain}: not a JSON object")
                return []

            skills = data.get("skills", [])
            if not isinstance(skills, list):
                logger.warning(f"Invalid manifest from {domain}: 'skills' is not a list")
                return []

            # Cache result
            self._cache[domain] = (now, skills)
            return skills

        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            logger.debug(f"Well-known fetch failed for {domain}: {e}")
            return []
        except Exception as e:
            logger.warning(f"Unexpected error fetching {domain}: {e}")
            return []

    def _to_search_result(self, skill_data: dict, domain: str) -> SkillSearchResult:
        """Convert a skill manifest entry to a SkillSearchResult."""
        return SkillSearchResult(
            id=skill_data.get("id", skill_data.get("name", "")),
            name=skill_data.get("name", ""),
            description=skill_data.get("description", ""),
            source=self.source_id,
            author=skill_data.get("author", domain),
            tags=skill_data.get("tags", []),
            source_url=skill_data.get("url", f"https://{domain}"),
            compatible_agents=skill_data.get("compatible_agents", []),
            metadata={
                "domain": domain,
                "version": skill_data.get("version"),
            },
        )
