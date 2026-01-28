"""
Lock File - Tracks installed skills with integrity verification.

Maintains a skills.lock.json file that records:
- Installed skills and their metadata
- SHA-256 content hashes for integrity verification
- Version counter for change tracking
- Atomic writes to prevent corruption
"""

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class LockedSkill:
    """A skill entry in the lock file."""

    name: str
    path: str
    content_hash: str  # SHA-256 of SKILL.md content
    source: str  # "auto", "graduated", "manual"
    locked_at: str  # ISO timestamp
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "path": self.path,
            "content_hash": self.content_hash,
            "source": self.source,
            "locked_at": self.locked_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LockedSkill":
        return cls(
            name=data["name"],
            path=data["path"],
            content_hash=data["content_hash"],
            source=data.get("source", "auto"),
            locked_at=data.get("locked_at", ""),
            metadata=data.get("metadata", {}),
        )


class LockFile:
    """Manages the skills lock file with integrity verification.

    Lock file path: ~/.claude/auto-skill/skills.lock.json
    """

    DEFAULT_PATH = Path.home() / ".claude" / "auto-skill" / "skills.lock.json"

    def __init__(self, path: Optional[Path] = None):
        self.path = path or self.DEFAULT_PATH
        self._data: dict = self._default_data()

    def _default_data(self) -> dict:
        return {
            "version": 0,
            "updated_at": "",
            "skills": {},
        }

    def load(self) -> "LockFile":
        """Load the lock file from disk.

        Returns:
            self (for chaining)
        """
        if self.path.exists():
            try:
                with open(self.path) as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._data = self._default_data()
        else:
            self._data = self._default_data()
        return self

    def save(self):
        """Save the lock file atomically (temp file + rename).

        Increments the version counter on each save.
        """
        self._data["version"] = self._data.get("version", 0) + 1
        self._data["updated_at"] = datetime.now(timezone.utc).isoformat()

        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: write to temp file, then rename
        fd, tmp_path = tempfile.mkstemp(
            dir=str(self.path.parent),
            suffix=".tmp",
            prefix=".skills.lock.",
        )
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(self._data, f, indent=2, default=str)
            os.replace(tmp_path, str(self.path))
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def add_skill(
        self,
        name: str,
        path: str,
        content: str,
        source: str = "auto",
        metadata: Optional[dict] = None,
    ):
        """Add or update a skill in the lock file.

        Args:
            name: Skill name.
            path: Path to the SKILL.md file.
            content: The SKILL.md file content (for hashing).
            source: Source of the skill.
            metadata: Optional metadata.
        """
        self._data.setdefault("skills", {})[name] = LockedSkill(
            name=name,
            path=path,
            content_hash=self._hash_content(content),
            source=source,
            locked_at=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        ).to_dict()

    def remove_skill(self, name: str) -> bool:
        """Remove a skill from the lock file.

        Returns:
            True if removed, False if not found.
        """
        skills = self._data.get("skills", {})
        if name in skills:
            del skills[name]
            return True
        return False

    def get_skill(self, name: str) -> Optional[LockedSkill]:
        """Get a locked skill by name."""
        skills = self._data.get("skills", {})
        if name in skills:
            return LockedSkill.from_dict(skills[name])
        return None

    def list_skills(self) -> list[LockedSkill]:
        """List all locked skills."""
        return [
            LockedSkill.from_dict(s)
            for s in self._data.get("skills", {}).values()
        ]

    def verify_integrity(self, name: str, content: str) -> bool:
        """Verify a skill's content matches its locked hash.

        Args:
            name: Skill name.
            content: Current SKILL.md content.

        Returns:
            True if content matches the locked hash, False if tampered.
        """
        skill = self.get_skill(name)
        if skill is None:
            return False
        return skill.content_hash == self._hash_content(content)

    def verify_all(self, skills_dir: Path) -> dict[str, bool]:
        """Verify integrity of all locked skills.

        Args:
            skills_dir: Root directory containing skill subdirectories.

        Returns:
            Dict mapping skill name -> integrity check result.
        """
        results = {}
        for locked in self.list_skills():
            skill_path = Path(locked.path)
            if skill_path.exists():
                content = skill_path.read_text()
                results[locked.name] = self.verify_integrity(locked.name, content)
            else:
                results[locked.name] = False
        return results

    @property
    def version(self) -> int:
        return self._data.get("version", 0)

    @property
    def skill_count(self) -> int:
        return len(self._data.get("skills", {}))

    @staticmethod
    def _hash_content(content: str) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()
