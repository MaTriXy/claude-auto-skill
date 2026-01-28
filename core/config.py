"""
Configuration management for Claude Auto-Skill.

Handles default settings and project-specific overrides.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class DetectionConfig:
    """Configuration for pattern detection."""

    min_occurrences: int = 3
    min_sequence_length: int = 2
    max_sequence_length: int = 10
    lookback_days: int = 7
    min_confidence: float = 0.7

    # Tools to ignore in pattern detection
    ignored_tools: list[str] = field(
        default_factory=lambda: [
            "AskUserQuestion",  # Interactive, not automatable
        ]
    )

    @classmethod
    def from_dict(cls, data: dict) -> "DetectionConfig":
        """Create config from dictionary."""
        return cls(
            min_occurrences=data.get("min_occurrences", 3),
            min_sequence_length=data.get("min_sequence_length", 2),
            max_sequence_length=data.get("max_sequence_length", 10),
            lookback_days=data.get("lookback_days", 7),
            min_confidence=data.get("min_confidence", 0.7),
            ignored_tools=data.get("ignored_tools", []),
        )


@dataclass
class AgentSettings:
    """Configuration for multi-agent support."""

    auto_detect: bool = True  # Auto-detect installed agents
    target_agents: list[str] = field(default_factory=list)  # Specific agent IDs to target
    symlink_skills: bool = True  # Create symlinks to share skills across agents

    @classmethod
    def from_dict(cls, data: dict) -> "AgentSettings":
        return cls(
            auto_detect=data.get("auto_detect", True),
            target_agents=data.get("target_agents", []),
            symlink_skills=data.get("symlink_skills", True),
        )


@dataclass
class ProviderSettings:
    """Configuration for skill providers."""

    enabled_providers: list[str] = field(default_factory=lambda: ["skillssh"])
    wellknown_domains: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "ProviderSettings":
        return cls(
            enabled_providers=data.get("enabled_providers", ["skillssh"]),
            wellknown_domains=data.get("wellknown_domains", []),
        )


@dataclass
class Config:
    """Full configuration for Auto-Skill."""

    detection: DetectionConfig = field(default_factory=DetectionConfig)
    agents: AgentSettings = field(default_factory=AgentSettings)
    providers: ProviderSettings = field(default_factory=ProviderSettings)
    db_path: Optional[Path] = None
    skills_output_dir: Optional[Path] = None
    enabled: bool = True

    # Project-specific overrides path
    LOCAL_CONFIG_FILE = ".claude/auto-skill.local.md"

    @classmethod
    def load(cls, project_path: Optional[Path] = None) -> "Config":
        """
        Load configuration with optional project overrides.

        Args:
            project_path: Path to project root for local overrides

        Returns:
            Config instance with merged settings
        """
        config = cls()

        # Check for project-local overrides
        if project_path:
            local_config_path = project_path / cls.LOCAL_CONFIG_FILE
            if local_config_path.exists():
                config = config.merge_local(local_config_path)

        return config

    def merge_local(self, local_path: Path) -> "Config":
        """Merge local configuration file."""
        try:
            content = local_path.read_text()

            # Extract YAML frontmatter from markdown
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    yaml_content = parts[1]
                    data = yaml.safe_load(yaml_content) or {}

                    # Merge detection config
                    if "detection" in data:
                        self.detection = DetectionConfig.from_dict(data["detection"])

                    # Merge agent config
                    if "agents" in data:
                        self.agents = AgentSettings.from_dict(data["agents"])

                    # Merge provider config
                    if "providers" in data:
                        self.providers = ProviderSettings.from_dict(data["providers"])

                    # Merge other settings
                    if "enabled" in data:
                        self.enabled = data["enabled"]

        except (OSError, yaml.YAMLError) as e:
            logger.warning(f"Failed to load config from {local_path}: {e}")

        return self

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            "detection": {
                "min_occurrences": self.detection.min_occurrences,
                "min_sequence_length": self.detection.min_sequence_length,
                "max_sequence_length": self.detection.max_sequence_length,
                "lookback_days": self.detection.lookback_days,
                "min_confidence": self.detection.min_confidence,
                "ignored_tools": self.detection.ignored_tools,
            },
            "enabled": self.enabled,
        }
