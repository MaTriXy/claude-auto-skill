"""Tests for agentskills.io spec compliance."""

import re
import pytest
from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.spec_validator import (
    validate_skill_md,
    SpecValidationResult,
    MAX_DESCRIPTION_LENGTH,
)
from core.skill_generator import SkillGenerator
from core.pattern_detector import DetectedPattern
from core.path_security import SPEC_NAME_REGEX, MAX_NAME_LENGTH


class TestSpecValidator:
    """Tests for the spec validator."""

    def test_valid_skill_passes(self):
        content = """---
name: my-skill
description: A valid skill
version: 1.0.0
allowed-tools:
  - Read
  - Write
---

# my-skill

A valid skill.
"""
        result = validate_skill_md(content)
        assert result.is_valid

    def test_missing_frontmatter_fails(self):
        result = validate_skill_md("# Just a heading\n\nNo frontmatter.")
        assert not result.is_valid

    def test_missing_name_fails(self):
        content = """---
description: No name
---
"""
        result = validate_skill_md(content)
        assert not result.is_valid
        assert any("name" in v.field for v in result.errors)

    def test_name_too_long_fails(self):
        content = f"""---
name: {"a" * 65}
description: Too long name
---
"""
        result = validate_skill_md(content)
        assert not result.is_valid
        assert any("name" in v.field for v in result.errors)

    def test_name_invalid_regex_fails(self):
        content = """---
name: My Skill
description: Invalid name
---
"""
        result = validate_skill_md(content)
        assert not result.is_valid

    def test_description_too_long_fails(self):
        content = f"""---
name: my-skill
description: {"x" * 1025}
---
"""
        result = validate_skill_md(content)
        assert not result.is_valid
        assert any("description" in v.field for v in result.errors)

    def test_allowed_tools_as_string_fails(self):
        content = """---
name: my-skill
description: Valid
allowed-tools: Read, Write, Edit
---
"""
        result = validate_skill_md(content)
        assert not result.is_valid
        assert any("allowed-tools" in v.field for v in result.errors)

    def test_allowed_tools_as_list_passes(self):
        content = """---
name: my-skill
description: Valid
version: 1.0.0
allowed-tools:
  - Read
  - Write
---
"""
        result = validate_skill_md(content)
        assert result.is_valid

    def test_missing_version_warns(self):
        content = """---
name: my-skill
description: Valid
---
"""
        result = validate_skill_md(content)
        # Version is a warning, not an error
        assert result.is_valid
        assert any("version" in v.field for v in result.warnings)


class TestGeneratedSkillCompliance:
    """Test that SkillGenerator output is spec-compliant."""

    @pytest.fixture
    def generator(self, tmp_path):
        return SkillGenerator(output_dir=tmp_path / "skills")

    @pytest.fixture
    def sample_pattern(self):
        return DetectedPattern(
            id="abc123def456",
            tool_sequence=["Grep", "Read", "Edit"],
            occurrence_count=5,
            confidence=0.85,
            session_ids=["session-1", "session-2"],
            first_seen=datetime(2024, 1, 1),
            last_seen=datetime(2024, 1, 15),
            success_rate=0.9,
            suggested_name="search-and-edit",
            suggested_description="Search for code, read context, then edit",
        )

    def test_generated_frontmatter_has_allowed_tools_as_list(self, generator, sample_pattern):
        candidate = generator.generate_candidate(sample_pattern)
        fm = candidate.yaml_frontmatter
        tools = fm.get("allowed-tools")
        assert isinstance(tools, list), f"allowed-tools should be list, got {type(tools)}"

    def test_generated_name_matches_spec_regex(self, generator, sample_pattern):
        candidate = generator.generate_candidate(sample_pattern)
        name = candidate.yaml_frontmatter["name"]
        assert SPEC_NAME_REGEX.match(name), f"'{name}' doesn't match spec regex"
        assert len(name) <= MAX_NAME_LENGTH

    def test_generated_description_under_1024(self, generator, sample_pattern):
        candidate = generator.generate_candidate(sample_pattern)
        desc = candidate.yaml_frontmatter["description"]
        assert len(desc) <= 1024

    def test_generated_skill_has_version(self, generator, sample_pattern):
        candidate = generator.generate_candidate(sample_pattern)
        assert "version" in candidate.yaml_frontmatter

    def test_full_render_passes_validation(self, generator, sample_pattern):
        candidate = generator.generate_candidate(sample_pattern)
        content = candidate.render()
        result = validate_skill_md(content)
        assert result.is_valid, f"Spec violations: {result.errors}"
