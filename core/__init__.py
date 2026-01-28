"""Claude Auto-Skill Core Modules."""

from .path_security import sanitize_name, is_path_safe, is_safe_symlink, safe_write
from .event_store import EventStore, ToolEvent
from .pattern_detector import PatternDetector, DetectedPattern
from .skill_generator import SkillGenerator, SkillCandidate
from .session_analyzer import SessionAnalyzer, SessionContext, ProblemSolvingPattern
from .lsp_analyzer import LSPAnalyzer, CodeStructure, CodeSymbol
from .design_pattern_detector import DesignPatternDetector, DesignPattern

from .agent_registry import AgentRegistry, AgentConfig
from .spec_validator import validate_skill_md, SpecValidationResult
from .lock_file import LockFile, LockedSkill
from .telemetry import (
    TelemetryCollector, TelemetryEvent, EffectivenessReport,
    track, is_telemetry_disabled,
)

# Hybrid integration (Phase 1 & 2)
from .mental_analyzer import MentalAnalyzer, MentalModel, MentalDomain, MentalCapability, MentalAspect, MentalDecision
from .skillssh_client import SkillsShClient, ExternalSkill
from .skill_tracker import SkillTracker, SkillAdoption
from .unified_suggester import UnifiedSuggester, SkillSuggestion

__all__ = [
    # Path security
    "sanitize_name",
    "is_path_safe",
    "is_safe_symlink",
    "safe_write",
    # Core
    "EventStore",
    "ToolEvent",
    "PatternDetector",
    "DetectedPattern",
    "SkillGenerator",
    "SkillCandidate",
    "SessionAnalyzer",
    "SessionContext",
    "ProblemSolvingPattern",
    "LSPAnalyzer",
    "CodeStructure",
    "CodeSymbol",
    "DesignPatternDetector",
    "DesignPattern",
    # Agent registry
    "AgentRegistry",
    "AgentConfig",
    # Spec validation
    "validate_skill_md",
    "SpecValidationResult",
    # Lock file
    "LockFile",
    "LockedSkill",
    # Telemetry
    "TelemetryCollector",
    "TelemetryEvent",
    "EffectivenessReport",
    "track",
    "is_telemetry_disabled",
    # Hybrid integration
    "MentalAnalyzer",
    "MentalModel",
    "MentalDomain",
    "MentalCapability",
    "MentalAspect",
    "MentalDecision",
    "SkillsShClient",
    "ExternalSkill",
    "SkillTracker",
    "SkillAdoption",
    "UnifiedSuggester",
    "SkillSuggestion",
]
