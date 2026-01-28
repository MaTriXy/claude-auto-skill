"""
Base provider protocol for skill discovery sources.

All skill providers must implement the SkillProvider protocol.
This enables pluggable discovery from different sources (Skills.sh,
local filesystem, well-known endpoints, etc.).
"""

from dataclasses import dataclass, field
from typing import Optional, Protocol, runtime_checkable


@dataclass
class SkillSearchResult:
    """A single skill result from a provider search."""

    id: str
    name: str
    description: str
    source: str  # provider identifier (e.g., "skillssh", "local", "wellknown")
    confidence: float = 0.5
    author: str = ""
    tags: list[str] = field(default_factory=list)
    install_count: int = 0
    source_url: str = ""
    compatible_agents: list[str] = field(default_factory=list)
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source": self.source,
            "confidence": self.confidence,
            "author": self.author,
            "tags": self.tags,
        }
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@runtime_checkable
class SkillProvider(Protocol):
    """Protocol for skill discovery providers.

    All providers must implement search(), get_skill_details(), and is_available().
    """

    @property
    def name(self) -> str:
        """Human-readable name of this provider (e.g., 'Skills.sh')."""
        ...

    @property
    def source_id(self) -> str:
        """Short identifier used in results (e.g., 'skillssh', 'local')."""
        ...

    def search(self, query: str, limit: int = 10) -> list[SkillSearchResult]:
        """Search for skills matching a query.

        Args:
            query: Search keywords.
            limit: Maximum number of results.

        Returns:
            List of matching SkillSearchResult objects.
        """
        ...

    def get_skill_details(self, skill_id: str) -> Optional[SkillSearchResult]:
        """Get detailed information about a specific skill.

        Args:
            skill_id: The skill identifier.

        Returns:
            SkillSearchResult with full details, or None if not found.
        """
        ...

    def is_available(self) -> bool:
        """Check if this provider is currently available.

        Returns:
            True if the provider can serve requests, False otherwise.
        """
        ...
