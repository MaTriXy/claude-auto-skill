"""Skill providers - pluggable skill discovery sources."""

from .base import SkillProvider, SkillSearchResult
from .skillssh_provider import SkillsShProvider
from .local_provider import LocalProvider
from .wellknown_provider import WellKnownProvider
from .manager import ProviderManager

__all__ = [
    "SkillProvider",
    "SkillSearchResult",
    "SkillsShProvider",
    "LocalProvider",
    "WellKnownProvider",
    "ProviderManager",
]
