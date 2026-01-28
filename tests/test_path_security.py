"""Tests for the path_security module."""

import os
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.path_security import sanitize_name, is_path_safe, is_safe_symlink, safe_write


class TestSanitizeName:
    """Tests for sanitize_name()."""

    def test_valid_name_passes_through(self):
        assert sanitize_name("my-skill") == "my-skill"

    def test_simple_kebab(self):
        assert sanitize_name("My Skill Name") == "my-skill-name"

    def test_underscores_converted(self):
        assert sanitize_name("my_skill_name") == "my-skill-name"

    def test_path_traversal_stripped(self):
        result = sanitize_name("../../../etc/passwd")
        assert ".." not in result
        assert "/" not in result
        assert result  # not empty

    def test_null_bytes_stripped(self):
        result = sanitize_name("my-skill\x00evil")
        assert "\x00" not in result
        assert "evil" in result

    def test_unicode_normalized(self):
        # NFKD decomposes accented chars; ASCII-compatible base letters are kept
        result = sanitize_name("café-résumé")
        assert result == "cafe-resume"

    def test_extremely_long_name_truncated(self):
        long_name = "a" * 200
        result = sanitize_name(long_name)
        assert len(result) <= 64

    def test_spec_regex_match(self):
        """All sanitized names must match ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$"""
        import re
        spec = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")

        names = [
            "hello-world",
            "My Complex_Name",
            "UPPERCASE",
            "with spaces and stuff",
            "a" * 100,
            "123-numeric-start",
        ]
        for name in names:
            result = sanitize_name(name)
            assert spec.match(result), f"'{result}' (from '{name}') doesn't match spec"

    def test_empty_name_raises(self):
        with pytest.raises(ValueError):
            sanitize_name("")

    def test_only_special_chars_raises(self):
        with pytest.raises(ValueError):
            sanitize_name("///...")

    def test_single_char(self):
        assert sanitize_name("a") == "a"

    def test_backslash_path(self):
        result = sanitize_name("foo\\bar\\baz")
        assert "\\" not in result
        assert result == "foo-bar-baz"


class TestIsPathSafe:
    """Tests for is_path_safe()."""

    def test_safe_path(self, tmp_path):
        target = tmp_path / "skills" / "my-skill" / "SKILL.md"
        assert is_path_safe(target, tmp_path) is True

    def test_path_traversal_blocked(self, tmp_path):
        target = tmp_path / ".." / "etc" / "passwd"
        assert is_path_safe(target, tmp_path) is False

    def test_null_byte_blocked(self, tmp_path):
        target = tmp_path / "skill\x00evil"
        assert is_path_safe(target, tmp_path) is False

    def test_exact_root_is_safe(self, tmp_path):
        assert is_path_safe(tmp_path, tmp_path) is True

    def test_outside_root_blocked(self, tmp_path):
        outside = tmp_path.parent / "other"
        assert is_path_safe(outside, tmp_path) is False

    def test_symlink_escape_blocked(self, tmp_path):
        """Symlink pointing outside root should be caught."""
        link = tmp_path / "link"
        try:
            link.symlink_to("/tmp")
            assert is_path_safe(link / "evil", tmp_path) is False
        except OSError:
            pytest.skip("Symlinks not supported on this platform")


class TestIsSafeSymlink:
    """Tests for is_safe_symlink()."""

    def test_safe_symlink(self, tmp_path):
        link = tmp_path / "link"
        target = tmp_path / "target"
        assert is_safe_symlink(link, target, tmp_path) is True

    def test_link_outside_root_blocked(self, tmp_path):
        link = tmp_path / ".." / "link"
        target = tmp_path / "target"
        assert is_safe_symlink(link, target, tmp_path) is False

    def test_target_outside_root_blocked(self, tmp_path):
        link = tmp_path / "link"
        target = Path("/etc/passwd")
        assert is_safe_symlink(link, target, tmp_path) is False


class TestSafeWrite:
    """Tests for safe_write()."""

    def test_safe_write_creates_file(self, tmp_path):
        target = tmp_path / "skills" / "my-skill" / "SKILL.md"
        result = safe_write("content", target, tmp_path)

        assert result.exists()
        assert result.read_text() == "content"

    def test_safe_write_creates_parents(self, tmp_path):
        target = tmp_path / "deep" / "nested" / "dir" / "file.md"
        safe_write("test", target, tmp_path)
        assert target.exists()

    def test_safe_write_rejects_traversal(self, tmp_path):
        target = tmp_path / ".." / "evil.md"
        with pytest.raises(ValueError, match="Unsafe path"):
            safe_write("evil", target, tmp_path)

    def test_safe_write_rejects_null_bytes(self, tmp_path):
        target = tmp_path / "file\x00evil.md"
        with pytest.raises(ValueError, match="Unsafe path"):
            safe_write("evil", target, tmp_path)
