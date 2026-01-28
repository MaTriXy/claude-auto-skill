"""
Agent Registry - Tracks compatible AI coding agents and their skill directories.

Detects installed agents, maps their skill directories, and enables
multi-agent skill output (Phase 4A).
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .path_security import is_path_safe, is_safe_symlink

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for a known AI coding agent."""

    id: str  # Short identifier (e.g., "claude-code")
    name: str  # Human-readable name
    skill_dir: Path  # Where this agent stores skills
    env_var: Optional[str] = None  # Env var that indicates this agent is running
    config_file: Optional[str] = None  # Config file that indicates installation
    description: str = ""

    @property
    def is_installed(self) -> bool:
        """Check if this agent appears to be installed."""
        # Check env var
        if self.env_var and os.environ.get(self.env_var):
            return True
        # Check config file existence
        if self.config_file:
            return Path(self.config_file).expanduser().exists()
        # Check skill directory existence
        return self.skill_dir.exists()


# Well-known agent configurations
_HOME = Path.home()

KNOWN_AGENTS: list[AgentConfig] = [
    AgentConfig(
        id="claude-code",
        name="Claude Code",
        skill_dir=_HOME / ".claude" / "skills",
        env_var="CLAUDE_SESSION_ID",
        config_file="~/.claude/settings.json",
        description="Anthropic's CLI for Claude",
    ),
    AgentConfig(
        id="opencode",
        name="OpenCode",
        skill_dir=_HOME / ".opencode" / "skills",
        config_file="~/.opencode/config.json",
        description="Open-source coding agent",
    ),
    AgentConfig(
        id="codex",
        name="Codex CLI",
        skill_dir=_HOME / ".codex" / "skills",
        config_file="~/.codex/config.yaml",
        description="OpenAI's Codex CLI agent",
    ),
    AgentConfig(
        id="continue",
        name="Continue",
        skill_dir=_HOME / ".continue" / "skills",
        config_file="~/.continue/config.json",
        description="Continue.dev IDE extension",
    ),
    AgentConfig(
        id="aider",
        name="Aider",
        skill_dir=_HOME / ".aider" / "skills",
        config_file="~/.aider.conf.yml",
        description="AI pair programming tool",
    ),
    AgentConfig(
        id="cursor",
        name="Cursor",
        skill_dir=_HOME / ".cursor" / "skills",
        config_file="~/.cursor/settings.json",
        description="AI-first code editor",
    ),
    AgentConfig(
        id="windsurf",
        name="Windsurf",
        skill_dir=_HOME / ".windsurf" / "skills",
        config_file="~/.windsurf/settings.json",
        description="Codeium's AI IDE",
    ),
    AgentConfig(
        id="cline",
        name="Cline",
        skill_dir=_HOME / ".cline" / "skills",
        config_file="~/.cline/config.json",
        description="AI coding agent for VS Code",
    ),
    AgentConfig(
        id="amp",
        name="Amp",
        skill_dir=_HOME / ".amp" / "skills",
        config_file="~/.amp/config.json",
        description="Sourcegraph's AI coding agent",
    ),
    AgentConfig(
        id="copilot",
        name="GitHub Copilot",
        skill_dir=_HOME / ".copilot" / "skills",
        config_file="~/.config/github-copilot/hosts.json",
        description="GitHub's AI coding assistant",
    ),
]


class AgentRegistry:
    """Registry of known AI coding agents.

    Detects installed agents, provides skill directory mappings,
    and supports multi-agent skill output.
    """

    def __init__(self, agents: Optional[list[AgentConfig]] = None):
        """Initialize the registry.

        Args:
            agents: List of agent configs. Defaults to KNOWN_AGENTS.
        """
        self._agents = {a.id: a for a in (agents or KNOWN_AGENTS)}

    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Get an agent configuration by ID."""
        return self._agents.get(agent_id)

    def list_agents(self) -> list[AgentConfig]:
        """List all known agents."""
        return list(self._agents.values())

    def detect_installed_agents(self) -> list[AgentConfig]:
        """Detect which agents are currently installed.

        Returns:
            List of AgentConfig for agents that appear to be installed.
        """
        return [a for a in self._agents.values() if a.is_installed]

    def get_agent_skill_dir(self, agent_id: str) -> Optional[Path]:
        """Get the skill directory for a specific agent.

        Args:
            agent_id: The agent identifier.

        Returns:
            Path to the agent's skill directory, or None if unknown.
        """
        agent = self._agents.get(agent_id)
        if agent:
            return agent.skill_dir
        return None

    def detect_current_agent(self) -> Optional[AgentConfig]:
        """Detect which agent is currently running based on environment.

        Returns:
            AgentConfig for the running agent, or None if undetectable.
        """
        for agent in self._agents.values():
            if agent.env_var and os.environ.get(agent.env_var):
                return agent
        return None

    def register_agent(self, agent: AgentConfig):
        """Register a new agent configuration.

        Args:
            agent: The agent configuration to register.
        """
        self._agents[agent.id] = agent

    def unregister_agent(self, agent_id: str) -> bool:
        """Remove an agent from the registry.

        Args:
            agent_id: The agent identifier.

        Returns:
            True if removed, False if not found.
        """
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False

    def create_skill_symlinks(
        self,
        skill_path: Path,
        skill_name: str,
        exclude_agent_id: Optional[str] = None,
        allowed_root: Optional[Path] = None,
    ) -> list[Path]:
        """Create symlinks to a skill in all installed agents' skill directories.

        Args:
            skill_path: The canonical skill file (or directory) to link to.
            skill_name: The skill name (used as the symlink directory name).
            exclude_agent_id: Agent to exclude (typically the source agent).
            allowed_root: Root directory for path safety checks. Defaults to
                the common parent of skill_path and all agent skill dirs.

        Returns:
            List of created symlink paths.
        """
        created = []

        # Determine allowed root: use filesystem root if not specified,
        # since we're linking across potentially different directory trees
        root = allowed_root or Path(skill_path.anchor)

        for agent in self.detect_installed_agents():
            if agent.id == exclude_agent_id:
                continue

            target_dir = agent.skill_dir / skill_name
            if target_dir.exists():
                continue

            # Validate the link target exists
            source = skill_path if skill_path.is_dir() else skill_path.parent
            if not source.exists():
                continue

            try:
                target_dir.parent.mkdir(parents=True, exist_ok=True)
                target_dir.symlink_to(source)
                created.append(target_dir)
                logger.info(f"Symlink created: {target_dir} -> {source}")
            except OSError as e:
                logger.warning(f"Failed to create symlink for {agent.name}: {e}")

        return created

    def remove_skill_symlinks(self, skill_name: str) -> int:
        """Remove symlinks for a skill from all agent directories.

        Args:
            skill_name: The skill name to remove symlinks for.

        Returns:
            Number of symlinks removed.
        """
        removed = 0
        for agent in self._agents.values():
            link_path = agent.skill_dir / skill_name
            if link_path.is_symlink():
                try:
                    link_path.unlink()
                    removed += 1
                    logger.info(f"Symlink removed: {link_path}")
                except OSError as e:
                    logger.warning(f"Failed to remove symlink {link_path}: {e}")
        return removed
