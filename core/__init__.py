"""
Claude Auto-Skill Core

Automatically detects workflow patterns and generates Claude Code skills.
"""

__version__ = "0.1.0"

from .event_store import EventStore
from .pattern_detector import PatternDetector
from .sequence_matcher import SequenceMatcher
from .skill_generator import SkillGenerator

__all__ = [
    "EventStore",
    "PatternDetector",
    "SequenceMatcher",
    "SkillGenerator",
]
