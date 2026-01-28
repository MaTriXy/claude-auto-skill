"""
Local Provider - Discovers skills from local filesystem directories.

Searches ~/.claude/skills/ and other agent-specific skill directories
for existing SKILL.md files.
"""

import yaml
from pathlib import Path
from typing import Optional

from .base import SkillProvider, SkillSearchResult


class LocalProvider:
    """SkillProvider that searches local filesystem skill directories."""

    def __init__(self, skill_dirs: Optional[list[Path]] = None):
        """Initialize with skill directories to search.

        Args:
            skill_dirs: List of directories containing skills.
                Defaults to ~/.claude/skills/.
        """
        if skill_dirs is None:
            skill_dirs = [Path.home() / ".claude" / "skills"]
        self._skill_dirs = skill_dirs

    @property
    def name(self) -> str:
        return "Local Skills"

    @property
    def source_id(self) -> str:
        return "local"

    def search(self, query: str, limit: int = 10) -> list[SkillSearchResult]:
        """Search local skill directories for matching skills.

        Matches against skill name, description, and tags.
        """
        results = []
        query_lower = query.lower()

        for skill_dir in self._skill_dirs:
            if not skill_dir.exists():
                continue

            for item in skill_dir.iterdir():
                if not item.is_dir():
                    continue
                skill_file = item / "SKILL.md"
                if not skill_file.exists():
                    continue

                result = self._parse_skill(skill_file)
                if result is None:
                    continue

                # Match against name, description, or tags
                searchable = f"{result.name} {result.description} {' '.join(result.tags)}".lower()
                if query_lower and query_lower not in searchable:
                    continue

                results.append(result)
                if len(results) >= limit:
                    break

        return results

    def get_skill_details(self, skill_id: str) -> Optional[SkillSearchResult]:
        """Get details for a local skill by name (used as ID)."""
        for skill_dir in self._skill_dirs:
            if not skill_dir.exists():
                continue
            skill_path = skill_dir / skill_id / "SKILL.md"
            if skill_path.exists():
                return self._parse_skill(skill_path)
        return None

    def is_available(self) -> bool:
        """Local provider is always available."""
        return True

    def _parse_skill(self, skill_file: Path) -> Optional[SkillSearchResult]:
        """Parse a SKILL.md file into a SkillSearchResult."""
        try:
            content = skill_file.read_text()
            if not content.startswith("---"):
                return None

            parts = content.split("---", 2)
            if len(parts) < 3:
                return None

            frontmatter = yaml.safe_load(parts[1]) or {}

            name = frontmatter.get("name", skill_file.parent.name)
            description = frontmatter.get("description", "")
            tags = frontmatter.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]

            return SkillSearchResult(
                id=name,
                name=name,
                description=description,
                source=self.source_id,
                confidence=frontmatter.get("confidence", 0.8),
                tags=tags,
                metadata={
                    "path": str(skill_file),
                    "auto_generated": frontmatter.get("auto-generated", False),
                },
            )
        except (OSError, yaml.YAMLError):
            return None
