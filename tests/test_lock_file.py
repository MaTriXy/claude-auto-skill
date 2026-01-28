"""Tests for the lock_file module."""

import json
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.lock_file import LockFile, LockedSkill


class TestLockFile:
    """Tests for LockFile class."""

    @pytest.fixture
    def lock(self, tmp_path):
        return LockFile(path=tmp_path / "skills.lock.json")

    def test_save_and_load(self, lock):
        lock.add_skill("my-skill", "/path/to/SKILL.md", "content", source="auto")
        lock.save()

        loaded = LockFile(path=lock.path).load()
        assert loaded.skill_count == 1
        assert loaded.get_skill("my-skill") is not None

    def test_version_increments(self, lock):
        assert lock.version == 0
        lock.save()
        assert lock.version == 1
        lock.save()
        assert lock.version == 2

    def test_add_skill(self, lock):
        lock.add_skill("test", "/path", "content")
        skill = lock.get_skill("test")
        assert skill is not None
        assert skill.name == "test"
        assert skill.content_hash  # Has a hash

    def test_remove_skill(self, lock):
        lock.add_skill("test", "/path", "content")
        assert lock.remove_skill("test") is True
        assert lock.get_skill("test") is None

    def test_remove_nonexistent(self, lock):
        assert lock.remove_skill("nonexistent") is False

    def test_list_skills(self, lock):
        lock.add_skill("skill-a", "/a", "a content")
        lock.add_skill("skill-b", "/b", "b content")
        skills = lock.list_skills()
        assert len(skills) == 2
        names = {s.name for s in skills}
        assert names == {"skill-a", "skill-b"}

    def test_verify_integrity_pass(self, lock):
        content = "---\nname: test\n---\n# test"
        lock.add_skill("test", "/path", content)
        assert lock.verify_integrity("test", content) is True

    def test_verify_integrity_tampered(self, lock):
        lock.add_skill("test", "/path", "original content")
        assert lock.verify_integrity("test", "tampered content") is False

    def test_verify_integrity_missing_skill(self, lock):
        assert lock.verify_integrity("nonexistent", "content") is False

    def test_verify_all(self, tmp_path):
        lock = LockFile(path=tmp_path / "lock.json")

        # Create a real skill file
        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        content = "---\nname: my-skill\n---"
        skill_file.write_text(content)

        lock.add_skill("my-skill", str(skill_file), content)

        results = lock.verify_all(tmp_path / "skills")
        assert results["my-skill"] is True

    def test_verify_all_detects_missing(self, tmp_path):
        lock = LockFile(path=tmp_path / "lock.json")
        lock.add_skill("gone", "/nonexistent/SKILL.md", "content")

        results = lock.verify_all(tmp_path)
        assert results["gone"] is False

    def test_atomic_write(self, lock):
        """Ensure no partial writes (lock file always valid JSON)."""
        lock.add_skill("test", "/path", "content")
        lock.save()

        # Verify file is valid JSON
        with open(lock.path) as f:
            data = json.load(f)
        assert "version" in data
        assert "skills" in data

    def test_load_nonexistent_file(self, tmp_path):
        lock = LockFile(path=tmp_path / "nonexistent.json")
        lock.load()
        assert lock.version == 0
        assert lock.skill_count == 0

    def test_load_corrupted_file(self, tmp_path):
        corrupted = tmp_path / "corrupted.json"
        corrupted.write_text("not json{{{")
        lock = LockFile(path=corrupted).load()
        assert lock.version == 0

    def test_skill_metadata(self, lock):
        lock.add_skill("test", "/path", "content", metadata={"key": "value"})
        skill = lock.get_skill("test")
        assert skill.metadata == {"key": "value"}


class TestLockedSkill:
    """Tests for LockedSkill dataclass."""

    def test_to_dict_roundtrip(self):
        skill = LockedSkill(
            name="test", path="/path", content_hash="abc123",
            source="auto", locked_at="2024-01-01T00:00:00",
            metadata={"key": "value"}
        )
        d = skill.to_dict()
        restored = LockedSkill.from_dict(d)
        assert restored.name == skill.name
        assert restored.content_hash == skill.content_hash
        assert restored.metadata == skill.metadata
