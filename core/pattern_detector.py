"""
Pattern Detector - Orchestrates pattern recognition and confidence scoring.

Analyzes tool usage events to detect reusable workflow patterns.
Uses multiple signals to calculate confidence:
- Repetition count (primary signal for MVP)
- Success rate of the pattern
- Recency of occurrences
- Consistency of tool inputs
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .event_store import EventStore, ToolEvent
from .sequence_matcher import SequenceMatcher, SequenceMatch


@dataclass
class DetectedPattern:
    """A detected workflow pattern with metadata."""

    id: str
    tool_sequence: list[str]
    occurrence_count: int
    confidence: float
    session_ids: list[str]
    first_seen: datetime
    last_seen: datetime
    success_rate: float = 1.0
    suggested_name: str = ""
    suggested_description: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tool_sequence": self.tool_sequence,
            "occurrence_count": self.occurrence_count,
            "confidence": self.confidence,
            "session_ids": self.session_ids,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "success_rate": self.success_rate,
            "suggested_name": self.suggested_name,
            "suggested_description": self.suggested_description,
        }


class PatternDetector:
    """Detects workflow patterns from tool usage events."""

    # Tool name mappings for generating readable names
    TOOL_VERBS = {
        "Read": "read",
        "Write": "write",
        "Edit": "edit",
        "Bash": "run",
        "Grep": "search",
        "Glob": "find",
        "WebFetch": "fetch",
        "WebSearch": "search",
        "Task": "delegate",
    }

    def __init__(self, store: EventStore):
        """
        Initialize the pattern detector.

        Args:
            store: EventStore instance for accessing events
        """
        self.store = store

    def detect_patterns(
        self,
        project_path: Optional[str] = None,
        min_occurrences: int = 3,
        min_sequence_length: int = 2,
        max_sequence_length: int = 10,
        lookback_days: int = 7,
    ) -> list[DetectedPattern]:
        """
        Detect workflow patterns in stored events.

        Args:
            project_path: Filter to specific project (None for all)
            min_occurrences: Minimum times pattern must appear
            min_sequence_length: Shortest pattern to detect
            max_sequence_length: Longest pattern to detect
            lookback_days: How many days back to analyze

        Returns:
            List of DetectedPattern objects, sorted by confidence
        """
        # Get tool sequences from the store
        sequences = self.store.get_tool_sequences(
            project_path=project_path,
            lookback_days=lookback_days,
            min_sequence_length=min_sequence_length,
        )

        if not sequences:
            return []

        # Find common subsequences
        matcher = SequenceMatcher(
            min_length=min_sequence_length,
            max_length=max_sequence_length,
            min_occurrences=min_occurrences,
        )

        matches = matcher.find_common_subsequences(sequences)

        if not matches:
            return []

        # Get full event data for richer analysis
        event_sessions = self.store.get_events_with_inputs(
            project_path=project_path,
            lookback_days=lookback_days,
        )

        # Convert matches to DetectedPatterns with confidence scores
        patterns = []
        for match in matches:
            pattern = self._create_pattern(match, event_sessions)
            if pattern:
                patterns.append(pattern)

        # Sort by confidence
        patterns.sort(key=lambda p: -p.confidence)

        return patterns

    def _create_pattern(
        self,
        match: SequenceMatch,
        event_sessions: list[list[ToolEvent]],
    ) -> Optional[DetectedPattern]:
        """Create a DetectedPattern from a SequenceMatch with full context."""
        if not match.session_indices:
            return None

        # Collect session IDs and timestamps
        session_ids = []
        first_seen = None
        last_seen = None
        success_count = 0
        total_count = 0

        for session_idx in match.session_indices:
            if session_idx >= len(event_sessions):
                continue

            events = event_sessions[session_idx]
            if events:
                session_ids.append(events[0].session_id)

                # Find this sequence in the session to get timestamps
                seq_events = self._find_sequence_in_session(match.sequence, events)
                if seq_events:
                    total_count += 1
                    if all(e.success for e in seq_events):
                        success_count += 1

                    seq_start = seq_events[0].timestamp
                    seq_end = seq_events[-1].timestamp

                    if first_seen is None or seq_start < first_seen:
                        first_seen = seq_start
                    if last_seen is None or seq_end > last_seen:
                        last_seen = seq_end

        if not first_seen or not last_seen:
            first_seen = datetime.now(timezone.utc)
            last_seen = datetime.now(timezone.utc)

        success_rate = success_count / total_count if total_count > 0 else 1.0

        # Calculate confidence score
        confidence = self._calculate_confidence(
            occurrence_count=match.occurrences,
            sequence_length=match.length,
            success_rate=success_rate,
            first_seen=first_seen,
            last_seen=last_seen,
        )

        # Generate suggested name and description
        suggested_name = self._generate_name(list(match.sequence))
        suggested_description = self._generate_description(list(match.sequence))

        return DetectedPattern(
            id=self._generate_pattern_id(match.sequence),
            tool_sequence=list(match.sequence),
            occurrence_count=match.occurrences,
            confidence=confidence,
            session_ids=list(set(session_ids)),
            first_seen=first_seen,
            last_seen=last_seen,
            success_rate=success_rate,
            suggested_name=suggested_name,
            suggested_description=suggested_description,
        )

    def _find_sequence_in_session(
        self,
        sequence: tuple[str, ...],
        events: list[ToolEvent],
    ) -> list[ToolEvent]:
        """Find events matching a sequence in a session."""
        tool_names = [e.tool_name for e in events]

        for start in range(len(tool_names) - len(sequence) + 1):
            if tuple(tool_names[start : start + len(sequence)]) == sequence:
                return events[start : start + len(sequence)]

        return []

    def _calculate_confidence(
        self,
        occurrence_count: int,
        sequence_length: int,
        success_rate: float,
        first_seen: datetime,
        last_seen: datetime,
    ) -> float:
        """
        Calculate a confidence score for a pattern.

        Factors:
        - Occurrence count: More occurrences = higher confidence
        - Sequence length: Moderate length patterns are most useful
        - Success rate: Higher success = higher confidence
        - Recency: Recent patterns are more relevant
        """
        # Base score from occurrences (logarithmic scale)
        import math

        occurrence_score = min(1.0, math.log(occurrence_count + 1) / math.log(10))

        # Length bonus: 3-5 tools is ideal
        if 3 <= sequence_length <= 5:
            length_score = 1.0
        elif sequence_length == 2:
            length_score = 0.7
        elif sequence_length > 5:
            length_score = max(0.5, 1.0 - (sequence_length - 5) * 0.1)
        else:
            length_score = 0.5

        # Success rate directly contributes
        success_score = success_rate

        # Recency: patterns used recently are more relevant
        days_since_last = (datetime.now(timezone.utc) - last_seen).days
        recency_score = max(0.5, 1.0 - days_since_last * 0.05)

        # Weighted combination
        confidence = (
            occurrence_score * 0.4
            + length_score * 0.2
            + success_score * 0.25
            + recency_score * 0.15
        )

        return min(1.0, max(0.0, confidence))

    def _generate_pattern_id(self, sequence: tuple[str, ...]) -> str:
        """Generate a unique ID for a pattern."""
        import hashlib

        seq_str = "-".join(sequence)
        return hashlib.sha256(seq_str.encode()).hexdigest()[:12]

    def _generate_name(self, tools: list[str]) -> str:
        """Generate a human-readable name for a pattern."""
        if not tools:
            return "unknown-workflow"

        # Use first and last tool to create name
        first_verb = self.TOOL_VERBS.get(tools[0], tools[0].lower())
        last_verb = self.TOOL_VERBS.get(tools[-1], tools[-1].lower())

        if len(tools) == 2:
            return f"{first_verb}-then-{last_verb}"
        else:
            return f"{first_verb}-and-{last_verb}"

    def _generate_description(self, tools: list[str]) -> str:
        """Generate a description for a pattern."""
        if not tools:
            return "Unknown workflow pattern"

        tool_list = ", ".join(tools)
        return f"Workflow pattern: {tool_list}"

    def get_pending_patterns(
        self,
        project_path: Optional[str] = None,
        min_confidence: float = 0.7,
    ) -> list[DetectedPattern]:
        """
        Get patterns that haven't been converted to skills yet.

        Checks against existing skills to avoid duplicates.
        """
        patterns = self.detect_patterns(project_path=project_path)

        # Filter by confidence
        patterns = [p for p in patterns if p.confidence >= min_confidence]

        # TODO: Check against existing skills to avoid duplicates

        return patterns
