"""
Session Analyzer - Analyzes full Claude Code session history.

Goes beyond tool patterns to understand:
- Full conversation context (user intents, Claude's reasoning)
- Decision-making patterns (how problems were approached)
- Problem-solving strategies (debugging, refactoring, TDD)
- Learning patterns (what worked, what didn't)
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .event_store import EventStore, ToolEvent


@dataclass
class ConversationTurn:
    """A single turn in the conversation (user message + Claude response)."""

    session_id: str
    timestamp: datetime
    user_message: Optional[str]
    claude_response: Optional[str]
    tools_used: list[str]
    intent_category: Optional[str] = None  # e.g., "debug", "refactor", "implement"
    problem_domain: Optional[str] = None  # e.g., "authentication", "API", "testing"
    outcome: Optional[str] = None  # "success", "partial", "failed"


@dataclass
class SessionContext:
    """Rich context for a complete session."""

    session_id: str
    start_time: datetime
    end_time: datetime
    project_path: str
    turns: list[ConversationTurn]
    primary_intent: Optional[str] = None
    problem_domains: list[str] = field(default_factory=list)
    workflow_type: Optional[str] = None  # "TDD", "refactor", "debug", "implement"
    success_indicators: dict = field(default_factory=dict)
    key_decisions: list[str] = field(default_factory=list)


@dataclass
class ProblemSolvingPattern:
    """A detected problem-solving approach pattern."""

    pattern_id: str
    pattern_type: str  # "TDD", "debug-cycle", "refactor-approach"
    description: str
    workflow_steps: list[str]
    success_rate: float
    occurrence_count: int
    example_sessions: list[str]
    contextual_indicators: dict = field(default_factory=dict)


class SessionAnalyzer:
    """Analyzes full session history for contextual understanding."""

    # Keywords for categorizing user intents
    INTENT_KEYWORDS = {
        "debug": ["bug", "error", "fix", "issue", "problem", "not working", "broken"],
        "implement": ["create", "add", "implement", "build", "make", "new feature"],
        "refactor": ["refactor", "clean up", "reorganize", "improve", "optimize"],
        "test": ["test", "TDD", "unit test", "testing", "coverage"],
        "explore": ["understand", "explain", "how does", "what is", "show me"],
        "document": ["document", "comment", "README", "docs", "documentation"],
    }

    # Workflow patterns based on tool sequences and context
    WORKFLOW_PATTERNS = {
        "TDD": {
            "tool_sequence": ["Write", "Bash", "Edit", "Bash"],
            "keywords": ["test", "TDD", "red-green-refactor"],
        },
        "debug-cycle": {
            "tool_sequence": ["Read", "Grep", "Bash", "Edit"],
            "keywords": ["error", "bug", "debug", "fix"],
        },
        "refactor-safe": {
            "tool_sequence": ["Read", "Edit", "Bash"],
            "keywords": ["refactor", "improve", "clean"],
        },
        "explore-then-implement": {
            "tool_sequence": ["Grep", "Read", "Write"],
            "keywords": ["understand", "then", "create"],
        },
    }

    def __init__(self, store: EventStore, session_data_path: Optional[Path] = None):
        """
        Initialize session analyzer.

        Args:
            store: EventStore instance for accessing tool events
            session_data_path: Optional path to full session conversation logs
        """
        self.store = store
        self.session_data_path = session_data_path or (
            Path.home() / ".claude" / "auto-skill" / "sessions"
        )
        self.session_data_path.mkdir(parents=True, exist_ok=True)

    def analyze_session(
        self, session_id: str, conversation_log: Optional[str] = None
    ) -> SessionContext:
        """
        Analyze a complete session with full context.

        Args:
            session_id: Session identifier
            conversation_log: Optional full conversation transcript

        Returns:
            SessionContext with rich analysis
        """
        # Get tool events for this session
        events = self.store.get_session_events(session_id)

        if not events:
            return self._create_empty_context(session_id)

        # Parse conversation turns if available
        turns = self._parse_conversation_turns(session_id, events, conversation_log)

        # Analyze intents and domains
        primary_intent = self._detect_primary_intent(turns)
        problem_domains = self._extract_problem_domains(turns, events)
        workflow_type = self._detect_workflow_type(events, turns)

        # Identify key decisions
        key_decisions = self._extract_key_decisions(turns)

        # Calculate success indicators
        success_indicators = self._calculate_success_indicators(events, turns)

        return SessionContext(
            session_id=session_id,
            start_time=events[0].timestamp,
            end_time=events[-1].timestamp,
            project_path=events[0].project_path,
            turns=turns,
            primary_intent=primary_intent,
            problem_domains=problem_domains,
            workflow_type=workflow_type,
            success_indicators=success_indicators,
            key_decisions=key_decisions,
        )

    def detect_problem_solving_patterns(
        self, lookback_days: int = 30, min_occurrences: int = 2
    ) -> list[ProblemSolvingPattern]:
        """
        Detect high-level problem-solving patterns across sessions.

        Args:
            lookback_days: Analysis window
            min_occurrences: Minimum times pattern must appear

        Returns:
            List of detected problem-solving patterns
        """
        # Get all sessions in the lookback window
        sessions = self._get_recent_sessions(lookback_days)

        # Analyze each session
        session_contexts = [
            self.analyze_session(sid) for sid in sessions
        ]

        # Group by workflow type
        workflow_groups = {}
        for ctx in session_contexts:
            if ctx.workflow_type:
                if ctx.workflow_type not in workflow_groups:
                    workflow_groups[ctx.workflow_type] = []
                workflow_groups[ctx.workflow_type].append(ctx)

        # Create patterns from groups
        patterns = []
        for workflow_type, contexts in workflow_groups.items():
            if len(contexts) >= min_occurrences:
                pattern = self._create_problem_solving_pattern(workflow_type, contexts)
                if pattern:
                    patterns.append(pattern)

        return sorted(patterns, key=lambda p: -p.success_rate)

    def _parse_conversation_turns(
        self, session_id: str, events: list[ToolEvent], conversation_log: Optional[str]
    ) -> list[ConversationTurn]:
        """Parse conversation into structured turns."""
        turns = []

        # If we have a full conversation log, parse it
        if conversation_log:
            # This would parse actual conversation logs
            # For now, we'll create turns based on tool events as proxy
            pass

        # Fallback: create turns from tool events
        # Group consecutive tools as part of the same turn
        current_turn_tools = []
        current_timestamp = None

        for event in events:
            if current_timestamp and (event.timestamp - current_timestamp).seconds > 60:
                # New turn (gap > 1 minute)
                if current_turn_tools:
                    turns.append(
                        ConversationTurn(
                            session_id=session_id,
                            timestamp=current_timestamp,
                            user_message=None,
                            claude_response=None,
                            tools_used=current_turn_tools,
                        )
                    )
                current_turn_tools = []

            current_turn_tools.append(event.tool_name)
            current_timestamp = event.timestamp

        # Don't forget the last turn
        if current_turn_tools:
            turns.append(
                ConversationTurn(
                    session_id=session_id,
                    timestamp=current_timestamp,
                    user_message=None,
                    claude_response=None,
                    tools_used=current_turn_tools,
                )
            )

        return turns

    def _detect_primary_intent(self, turns: list[ConversationTurn]) -> Optional[str]:
        """Detect the primary user intent for the session."""
        if not turns:
            return None

        # Count intent keywords across all user messages
        intent_scores = {intent: 0 for intent in self.INTENT_KEYWORDS}

        for turn in turns:
            if turn.user_message:
                message_lower = turn.user_message.lower()
                for intent, keywords in self.INTENT_KEYWORDS.items():
                    for keyword in keywords:
                        if keyword in message_lower:
                            intent_scores[intent] += 1

        # Return intent with highest score
        if max(intent_scores.values()) > 0:
            return max(intent_scores.items(), key=lambda x: x[1])[0]

        return None

    def _extract_problem_domains(
        self, turns: list[ConversationTurn], events: list[ToolEvent]
    ) -> list[str]:
        """Extract problem domains from file paths and conversation."""
        domains = set()

        # Extract from file paths in tool inputs
        for event in events:
            if "path" in event.tool_input or "file_path" in event.tool_input:
                path = event.tool_input.get("path") or event.tool_input.get("file_path")
                if path:
                    # Extract domain from path (e.g., "auth" from "src/auth/login.py")
                    parts = Path(path).parts
                    if len(parts) > 1:
                        domains.add(parts[-2])  # Parent directory as domain

        return sorted(list(domains))[:5]  # Top 5 domains

    def _detect_workflow_type(
        self, events: list[ToolEvent], turns: list[ConversationTurn]
    ) -> Optional[str]:
        """Detect the type of workflow (TDD, debug, refactor, etc)."""
        tool_sequence = [e.tool_name for e in events]

        # Check against known workflow patterns
        for workflow_type, pattern_info in self.WORKFLOW_PATTERNS.items():
            pattern_seq = pattern_info["tool_sequence"]

            # Check if pattern appears in sequence
            if self._contains_subsequence(tool_sequence, pattern_seq):
                return workflow_type

        return None

    def _contains_subsequence(self, sequence: list, subsequence: list) -> bool:
        """Check if subsequence appears in sequence."""
        sub_len = len(subsequence)
        return any(
            sequence[i : i + sub_len] == subsequence
            for i in range(len(sequence) - sub_len + 1)
        )

    def _extract_key_decisions(self, turns: list[ConversationTurn]) -> list[str]:
        """Extract key decisions made during the session."""
        # Placeholder for decision extraction logic
        # Would analyze conversation for decision points
        return []

    def _calculate_success_indicators(
        self, events: list[ToolEvent], turns: list[ConversationTurn]
    ) -> dict:
        """Calculate indicators of session success."""
        total_tools = len(events)
        successful_tools = sum(1 for e in events if e.success)

        return {
            "tool_success_rate": successful_tools / total_tools if total_tools > 0 else 0,
            "total_tools_used": total_tools,
            "session_duration_minutes": (
                (events[-1].timestamp - events[0].timestamp).seconds / 60
                if events
                else 0
            ),
        }

    def _get_recent_sessions(self, lookback_days: int) -> list[str]:
        """Get list of session IDs from recent activity."""
        sequences = self.store.get_events_with_inputs(lookback_days=lookback_days)
        return list(set(events[0].session_id for events in sequences if events))

    def _create_problem_solving_pattern(
        self, workflow_type: str, contexts: list[SessionContext]
    ) -> Optional[ProblemSolvingPattern]:
        """Create a problem-solving pattern from similar contexts."""
        if not contexts:
            return None

        # Calculate success rate
        success_count = sum(
            1
            for ctx in contexts
            if ctx.success_indicators.get("tool_success_rate", 0) > 0.8
        )
        success_rate = success_count / len(contexts)

        # Extract common workflow steps
        workflow_steps = self._extract_common_workflow_steps(contexts)

        # Get pattern info
        pattern_info = self.WORKFLOW_PATTERNS.get(workflow_type, {})

        return ProblemSolvingPattern(
            pattern_id=f"ps-{workflow_type}",
            pattern_type=workflow_type,
            description=f"Problem-solving pattern: {workflow_type}",
            workflow_steps=workflow_steps,
            success_rate=success_rate,
            occurrence_count=len(contexts),
            example_sessions=[ctx.session_id for ctx in contexts[:3]],
            contextual_indicators={
                "primary_intents": list(
                    set(ctx.primary_intent for ctx in contexts if ctx.primary_intent)
                ),
                "common_domains": self._get_common_domains(contexts),
            },
        )

    def _extract_common_workflow_steps(
        self, contexts: list[SessionContext]
    ) -> list[str]:
        """Extract common workflow steps across contexts."""
        # Placeholder - would do more sophisticated analysis
        return ["Analyze problem", "Plan approach", "Implement solution", "Verify"]

    def _get_common_domains(self, contexts: list[SessionContext]) -> list[str]:
        """Get most common problem domains across contexts."""
        all_domains = []
        for ctx in contexts:
            all_domains.extend(ctx.problem_domains)

        # Count and return top domains
        from collections import Counter

        return [domain for domain, _ in Counter(all_domains).most_common(3)]

    def _create_empty_context(self, session_id: str) -> SessionContext:
        """Create an empty session context."""
        now = datetime.now(timezone.utc)
        return SessionContext(
            session_id=session_id,
            start_time=now,
            end_time=now,
            project_path="",
            turns=[],
        )

    def save_session_analysis(self, context: SessionContext) -> Path:
        """Save session analysis to disk for future reference."""
        output_path = self.session_data_path / f"{context.session_id}.json"

        data = {
            "session_id": context.session_id,
            "start_time": context.start_time.isoformat(),
            "end_time": context.end_time.isoformat(),
            "project_path": context.project_path,
            "primary_intent": context.primary_intent,
            "problem_domains": context.problem_domains,
            "workflow_type": context.workflow_type,
            "success_indicators": context.success_indicators,
            "key_decisions": context.key_decisions,
            "turn_count": len(context.turns),
        }

        output_path.write_text(json.dumps(data, indent=2))
        return output_path
