"""Tests for the SkillGenerator module."""

import tempfile
import pytest
from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.pattern_detector import DetectedPattern
from core.skill_generator import SkillGenerator, SkillCandidate


class TestSkillGenerator:
    """Tests for SkillGenerator class."""

    @pytest.fixture
    def generator(self, tmp_path):
        """Create a SkillGenerator with temp output directory."""
        return SkillGenerator(output_dir=tmp_path / "skills")

    @pytest.fixture
    def sample_pattern(self):
        """Create a sample DetectedPattern for testing."""
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

    def test_generate_candidate(self, generator, sample_pattern):
        """Test generating a skill candidate from a pattern."""
        candidate = generator.generate_candidate(sample_pattern)

        assert candidate.pattern == sample_pattern
        assert candidate.name  # Has a name
        assert candidate.description  # Has a description
        assert len(candidate.steps) == 3  # One step per tool
        assert candidate.yaml_frontmatter["auto-generated"] is True
        assert "confidence" in candidate.yaml_frontmatter

    def test_generate_skill_name(self, generator, sample_pattern):
        """Test skill name generation."""
        name = generator._generate_skill_name(sample_pattern)

        # Should be kebab-case and include pattern ID fragment
        assert "-" in name
        assert name.islower() or "-" in name
        assert sample_pattern.id[:6] in name

    def test_generate_steps(self, generator, sample_pattern):
        """Test procedural step generation."""
        steps = generator._generate_steps(sample_pattern)

        assert len(steps) == 3
        assert all(step.startswith(str(i + 1)) for i, step in enumerate(steps))

    def test_save_skill(self, generator, sample_pattern):
        """Test saving a skill to disk."""
        candidate = generator.generate_candidate(sample_pattern)
        path = generator.save_skill(candidate)

        assert path.exists()
        assert path.name == "SKILL.md"

        content = path.read_text()
        assert "---" in content  # Has frontmatter
        assert "auto-generated: true" in content
        assert sample_pattern.id in content

    def test_render_skill_md(self):
        """Test static SKILL.md rendering."""
        content = SkillGenerator.render_skill_md(
            name="test-skill",
            description="A test skill for testing",
            steps=["1. First step", "2. Second step"],
            frontmatter={
                "name": "test-skill",
                "description": "A test skill",
                "auto-generated": True,
            },
        )

        assert "---" in content
        assert "test-skill" in content
        assert "1. First step" in content
        assert "2. Second step" in content

    def test_list_generated_skills_empty(self, generator):
        """Test listing skills when none exist."""
        skills = generator.list_generated_skills()
        assert skills == []

    def test_list_generated_skills(self, generator, sample_pattern):
        """Test listing generated skills."""
        # Generate and save a skill
        candidate = generator.generate_candidate(sample_pattern)
        generator.save_skill(candidate)

        skills = generator.list_generated_skills()
        assert len(skills) == 1
        assert skills[0].name == "SKILL.md"

    def test_delete_skill(self, generator, sample_pattern):
        """Test deleting a skill."""
        # Generate and save a skill
        candidate = generator.generate_candidate(sample_pattern)
        generator.save_skill(candidate)

        # Delete it
        result = generator.delete_skill(candidate.name)
        assert result is True

        # Should be gone
        skills = generator.list_generated_skills()
        assert len(skills) == 0

    def test_delete_nonexistent_skill(self, generator):
        """Test deleting a skill that doesn't exist."""
        result = generator.delete_skill("nonexistent-skill")
        assert result is False


class TestSkillCandidate:
    """Tests for SkillCandidate dataclass."""

    def test_render(self, tmp_path):
        """Test rendering a skill candidate."""
        pattern = DetectedPattern(
            id="test123",
            tool_sequence=["Read", "Write"],
            occurrence_count=3,
            confidence=0.75,
            session_ids=["s1"],
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
        )

        candidate = SkillCandidate(
            pattern=pattern,
            name="test-skill",
            description="Test description",
            steps=["1. Read file", "2. Write file"],
            output_path=tmp_path / "test-skill" / "SKILL.md",
            yaml_frontmatter={
                "name": "test-skill",
                "description": "Test description",
                "auto-generated": True,
            },
        )

        content = candidate.render()

        assert "---" in content
        assert "test-skill" in content
        assert "Test description" in content
