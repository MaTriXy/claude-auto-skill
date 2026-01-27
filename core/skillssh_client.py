"""
Skills.sh API Client - Integrates Vercel's external skill discovery.

Provides access to the skills.sh community skill registry:
- Search for skills by query
- Get trending skills
- Fetch skill details

API Endpoint: https://skills.sh
"""

import json
import urllib.request
import urllib.parse
import urllib.error
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExternalSkill:
    """An external skill from skills.sh registry."""

    id: str
    name: str
    description: str
    author: str
    install_count: int
    tags: list[str] = field(default_factory=list)
    source_url: str = ""

    # Compatibility
    compatible_agents: list[str] = field(default_factory=list)

    # Metadata
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "install_count": self.install_count,
            "tags": self.tags,
            "source_url": self.source_url,
            "compatible_agents": self.compatible_agents,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class SkillsShClient:
    """
    Client for skills.sh API.

    Provides methods to discover and fetch external skills from the
    Vercel skills.sh community registry.
    """

    BASE_URL = "https://skills.sh"

    def __init__(self, timeout: int = 10):
        """
        Initialize Skills.sh client.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout

    def search(self, query: str, limit: int = 10) -> list[ExternalSkill]:
        """
        Search for skills by query.

        Args:
            query: Search query (keywords, tags, etc.)
            limit: Maximum number of results

        Returns:
            List of matching ExternalSkill objects
        """
        try:
            params = urllib.parse.urlencode({"q": query, "limit": limit})
            url = f"{self.BASE_URL}/api/skills/search?{params}"

            with urllib.request.urlopen(url, timeout=self.timeout) as response:
                data = json.loads(response.read().decode())

            skills = []
            for item in data.get("skills", []):
                skills.append(self._parse_skill(item))

            return skills

        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            print(f"[Skills.sh] Search failed: {e}")
            return []
        except Exception as e:
            print(f"[Skills.sh] Unexpected error during search: {e}")
            return []

    def get_trending(self, limit: int = 20) -> list[ExternalSkill]:
        """
        Get trending skills.

        Args:
            limit: Maximum number of results

        Returns:
            List of trending ExternalSkill objects
        """
        try:
            url = f"{self.BASE_URL}/api/skills/trending?limit={limit}"

            with urllib.request.urlopen(url, timeout=self.timeout) as response:
                data = json.loads(response.read().decode())

            skills = []
            for item in data.get("skills", []):
                skills.append(self._parse_skill(item))

            return skills

        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            print(f"[Skills.sh] Get trending failed: {e}")
            return []
        except Exception as e:
            print(f"[Skills.sh] Unexpected error during get trending: {e}")
            return []

    def get_skill_details(self, skill_id: str) -> Optional[ExternalSkill]:
        """
        Get detailed information about a specific skill.

        Args:
            skill_id: Skill identifier

        Returns:
            ExternalSkill with full details, or None if not found
        """
        try:
            url = f"{self.BASE_URL}/api/skills/{skill_id}"

            with urllib.request.urlopen(url, timeout=self.timeout) as response:
                item = json.loads(response.read().decode())

            return self._parse_skill(item)

        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            print(f"[Skills.sh] Get details failed: {e}")
            return None
        except Exception as e:
            print(f"[Skills.sh] Unexpected error during get details: {e}")
            return None

    def get_skills_by_tag(self, tag: str, limit: int = 10) -> list[ExternalSkill]:
        """
        Get skills by tag.

        Args:
            tag: Tag to filter by (e.g., "payment", "authentication")
            limit: Maximum number of results

        Returns:
            List of matching ExternalSkill objects
        """
        try:
            params = urllib.parse.urlencode({"tag": tag, "limit": limit})
            url = f"{self.BASE_URL}/api/skills/by-tag?{params}"

            with urllib.request.urlopen(url, timeout=self.timeout) as response:
                data = json.loads(response.read().decode())

            skills = []
            for item in data.get("skills", []):
                skills.append(self._parse_skill(item))

            return skills

        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            print(f"[Skills.sh] Get by tag failed: {e}")
            return []
        except Exception as e:
            print(f"[Skills.sh] Unexpected error during get by tag: {e}")
            return []

    def _parse_skill(self, item: dict) -> ExternalSkill:
        """
        Parse skill data from API response.

        Args:
            item: Raw skill data from API

        Returns:
            ExternalSkill object
        """
        return ExternalSkill(
            id=item.get("id", ""),
            name=item.get("name", ""),
            description=item.get("description", ""),
            author=item.get("author", "unknown"),
            install_count=item.get("installCount", 0),
            tags=item.get("tags", []),
            source_url=item.get("sourceUrl", ""),
            compatible_agents=item.get("compatibleAgents", []),
            created_at=item.get("createdAt"),
            updated_at=item.get("updatedAt")
        )

    def is_available(self) -> bool:
        """
        Check if skills.sh API is available.

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            url = f"{self.BASE_URL}/api/health"
            with urllib.request.urlopen(url, timeout=5) as response:
                return response.status == 200
        except:
            return False
