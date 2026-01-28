"""Tests for the agent_registry module."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent_registry import AgentConfig, AgentRegistry, KNOWN_AGENTS


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_is_installed_via_env_var(self):
        agent = AgentConfig(
            id="test", name="Test", skill_dir=Path("/tmp/nonexistent"),
            env_var="TEST_AGENT_RUNNING"
        )
        with patch.dict(os.environ, {"TEST_AGENT_RUNNING": "1"}):
            assert agent.is_installed is True

    def test_is_installed_via_config_file(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        agent = AgentConfig(
            id="test", name="Test", skill_dir=Path("/tmp/nonexistent"),
            config_file=str(config_file)
        )
        assert agent.is_installed is True

    def test_is_installed_via_skill_dir(self, tmp_path):
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()
        agent = AgentConfig(
            id="test", name="Test", skill_dir=skill_dir
        )
        assert agent.is_installed is True

    def test_is_not_installed(self):
        agent = AgentConfig(
            id="test", name="Test", skill_dir=Path("/tmp/nonexistent_skills_dir_xyz")
        )
        assert agent.is_installed is False


class TestAgentRegistry:
    """Tests for AgentRegistry class."""

    @pytest.fixture
    def registry(self, tmp_path):
        agents = [
            AgentConfig(
                id="agent-a", name="Agent A",
                skill_dir=tmp_path / "a" / "skills",
                env_var="AGENT_A_RUNNING"
            ),
            AgentConfig(
                id="agent-b", name="Agent B",
                skill_dir=tmp_path / "b" / "skills",
            ),
        ]
        return AgentRegistry(agents=agents)

    def test_list_agents(self, registry):
        agents = registry.list_agents()
        assert len(agents) == 2
        assert agents[0].id == "agent-a"

    def test_get_agent(self, registry):
        agent = registry.get_agent("agent-a")
        assert agent is not None
        assert agent.name == "Agent A"

    def test_get_agent_not_found(self, registry):
        assert registry.get_agent("nonexistent") is None

    def test_get_agent_skill_dir(self, registry):
        skill_dir = registry.get_agent_skill_dir("agent-a")
        assert skill_dir is not None
        assert "skills" in str(skill_dir)

    def test_get_agent_skill_dir_not_found(self, registry):
        assert registry.get_agent_skill_dir("nonexistent") is None

    def test_detect_installed_agents(self, registry, tmp_path):
        # Make agent-b's skill dir exist
        (tmp_path / "b" / "skills").mkdir(parents=True)
        installed = registry.detect_installed_agents()
        assert any(a.id == "agent-b" for a in installed)

    def test_detect_current_agent(self, registry):
        with patch.dict(os.environ, {"AGENT_A_RUNNING": "1"}):
            current = registry.detect_current_agent()
            assert current is not None
            assert current.id == "agent-a"

    def test_detect_current_agent_none(self, registry):
        current = registry.detect_current_agent()
        assert current is None

    def test_register_agent(self, registry, tmp_path):
        new_agent = AgentConfig(
            id="agent-c", name="Agent C",
            skill_dir=tmp_path / "c" / "skills"
        )
        registry.register_agent(new_agent)
        assert registry.get_agent("agent-c") is not None

    def test_unregister_agent(self, registry):
        assert registry.unregister_agent("agent-a") is True
        assert registry.get_agent("agent-a") is None

    def test_unregister_agent_not_found(self, registry):
        assert registry.unregister_agent("nonexistent") is False

    def test_known_agents_well_formed(self):
        """Verify KNOWN_AGENTS are all properly defined."""
        for agent in KNOWN_AGENTS:
            assert agent.id
            assert agent.name
            assert agent.skill_dir
