"""
Skills.sh provider - wraps the existing SkillsShClient as a SkillProvider.

Adapts the legacy SkillsShClient to the new SkillProvider protocol.
"""

from typing import Optional

from ..skillssh_client import SkillsShClient, ExternalSkill
from .base import SkillProvider, SkillSearchResult


class SkillsShProvider:
    """SkillProvider implementation backed by the Skills.sh API."""

    def __init__(self, client: Optional[SkillsShClient] = None):
        self._client = client or SkillsShClient()

    @property
    def name(self) -> str:
        return "Skills.sh"

    @property
    def source_id(self) -> str:
        return "skillssh"

    def search(self, query: str, limit: int = 10) -> list[SkillSearchResult]:
        external_skills = self._client.search(query, limit=limit)
        return [self._to_search_result(s) for s in external_skills]

    def get_skill_details(self, skill_id: str) -> Optional[SkillSearchResult]:
        ext = self._client.get_skill_details(skill_id)
        if ext is None:
            return None
        return self._to_search_result(ext)

    def is_available(self) -> bool:
        return self._client.is_available()

    def _to_search_result(self, ext: ExternalSkill) -> SkillSearchResult:
        return SkillSearchResult(
            id=ext.id,
            name=ext.name,
            description=ext.description,
            source=self.source_id,
            author=ext.author,
            tags=ext.tags,
            install_count=ext.install_count,
            source_url=ext.source_url,
            compatible_agents=ext.compatible_agents,
            metadata={
                "created_at": ext.created_at,
                "updated_at": ext.updated_at,
            },
        )
