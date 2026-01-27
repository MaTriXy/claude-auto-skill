"""Claude Auto-Skill Core Modules."""

from .event_store import EventStore, ToolEvent
from .pattern_detector import PatternDetector, DetectedPattern
from .skill_generator import SkillGenerator, SkillCandidate
from .session_analyzer import SessionAnalyzer, SessionContext, ProblemSolvingPattern
from .lsp_analyzer import LSPAnalyzer, CodeStructure, CodeSymbol
from .design_pattern_detector import DesignPatternDetector, DesignPattern

# Hybrid integration (Phase 1 & 2)
from .mental_analyzer import MentalAnalyzer, MentalModel, MentalDomain, MentalCapability, MentalAspect, MentalDecision
from .skillssh_client import SkillsShClient, ExternalSkill
from .skill_tracker import SkillTracker, SkillAdoption
from .unified_suggester import UnifiedSuggester, SkillSuggestion

__all__ = [
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
