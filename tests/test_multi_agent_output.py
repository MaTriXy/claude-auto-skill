"""Tests for multi-agent skill output (symlinks)."""

import os
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent_registry import AgentConfig, AgentRegistry
from core.path_security import is_safe_symlink


class TestCreateSkillSymlinks:
    """Tests for AgentRegistry.create_skill_symlinks()."""

    @pytest.fixture
    def setup(self, tmp_path):
        """Set up agents with skill dirs."""
        # Create agent skill dirs
        agent_a_dir = tmp_path / "agent-a" / "skills"
        agent_b_dir = tmp_path / "agent-b" / "skills"
        agent_a_dir.mkdir(parents=True)
        agent_b_dir.mkdir(parents=True)

        agents = [
            AgentConfig(id="agent-a", name="Agent A", skill_dir=agent_a_dir),
            AgentConfig(id="agent-b", name="Agent B", skill_dir=agent_b_dir),
        ]
        registry = AgentRegistry(agents=agents)

        # Create a skill file in agent-a
        skill_dir = agent_a_dir / "my-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("---\nname: my-skill\n---\n# my-skill\n")

        return registry, skill_file, agent_a_dir, agent_b_dir

    def test_creates_symlink_in_other_agent(self, setup):
        registry, skill_file, agent_a_dir, agent_b_dir = setup
        created = registry.create_skill_symlinks(
            skill_path=skill_file,
            skill_name="my-skill",
            exclude_agent_id="agent-a",
        )
        assert len(created) == 1
        assert created[0] == agent_b_dir / "my-skill"
        assert created[0].is_symlink()

    def test_excludes_source_agent(self, setup):
        registry, skill_file, agent_a_dir, agent_b_dir = setup
        created = registry.create_skill_symlinks(
            skill_path=skill_file,
            skill_name="my-skill",
            exclude_agent_id="agent-a",
        )
        # Should not create in agent-a
        assert not (agent_a_dir / "my-skill-link").is_symlink()

    def test_skips_existing_dir(self, setup):
        registry, skill_file, agent_a_dir, agent_b_dir = setup
        # Pre-create the target
        (agent_b_dir / "my-skill").mkdir()
        created = registry.create_skill_symlinks(
            skill_path=skill_file,
            skill_name="my-skill",
            exclude_agent_id="agent-a",
        )
        assert len(created) == 0

    def test_no_agents_installed(self, tmp_path):
        agents = [
            AgentConfig(
                id="absent",
                name="Absent",
                skill_dir=tmp_path / "nonexistent" / "skills",
            ),
        ]
        registry = AgentRegistry(agents=agents)
        created = registry.create_skill_symlinks(
            skill_path=tmp_path / "skill" / "SKILL.md",
            skill_name="test-skill",
        )
        assert len(created) == 0


class TestRemoveSkillSymlinks:
    """Tests for AgentRegistry.remove_skill_symlinks()."""

    def test_removes_symlinks(self, tmp_path):
        agent_dir = tmp_path / "agent" / "skills"
        agent_dir.mkdir(parents=True)

        # Create a symlink
        link = agent_dir / "my-skill"
        source = tmp_path / "source"
        source.mkdir()
        link.symlink_to(source)

        agents = [AgentConfig(id="agent", name="Agent", skill_dir=agent_dir)]
        registry = AgentRegistry(agents=agents)

        removed = registry.remove_skill_symlinks("my-skill")
        assert removed == 1
        assert not link.exists()

    def test_ignores_non_symlinks(self, tmp_path):
        agent_dir = tmp_path / "agent" / "skills"
        real_dir = agent_dir / "my-skill"
        real_dir.mkdir(parents=True)

        agents = [AgentConfig(id="agent", name="Agent", skill_dir=agent_dir)]
        registry = AgentRegistry(agents=agents)

        removed = registry.remove_skill_symlinks("my-skill")
        assert removed == 0
        assert real_dir.exists()  # Not removed


class TestIsSafeSymlink:
    """Tests for is_safe_symlink in multi-agent context."""

    def test_safe_within_home(self, tmp_path):
        link = tmp_path / "link"
        target = tmp_path / "target"
        assert is_safe_symlink(link, target, tmp_path) is True

    def test_target_outside_root_blocked(self, tmp_path):
        link = tmp_path / "link"
        target = Path("/etc/passwd")
        assert is_safe_symlink(link, target, tmp_path) is False
