"""
Pattern Detector - Enhanced v2 with session analysis, LSP, and design patterns.

V1 Functionality (preserved):
- Detects tool usage patterns from event store
- Calculates confidence scores
- Generates pattern IDs

V2 Enhancements (new):
- Integrates session context analysis
- Incorporates code structure insights from LSP
- Detects design patterns (architectural, coding, workflow)
- Provides richer metadata for skill generation
"""

import hashlib
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .event_store import EventStore, ToolEvent
from .sequence_matcher import SequenceMatcher, SequenceMatch

# V2 imports
try:
    from .session_analyzer import SessionAnalyzer, SessionContext
    from .lsp_analyzer import LSPAnalyzer, CodeStructure
    from .design_pattern_detector import DesignPatternDetector, DesignPattern

    V2_AVAILABLE = True
except ImportError:
    V2_AVAILABLE = False


@dataclass
class DetectedPattern:
    """A detected workflow pattern with v1 + v2 metadata."""

    # V1 fields
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

    # V2 enhancements
    session_context: Optional[dict] = None  # From SessionAnalyzer
    code_context: Optional[dict] = None  # From LSPAnalyzer
    design_patterns: list[dict] = field(default_factory=list)  # From DesignPatternDetector
    problem_solving_approach: Optional[dict] = None  # Workflow strategy

    def to_dict(self) -> dict:
        """Convert to dictionary with v1 + v2 data."""
        base = {
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

        # Add v2 fields if present
        if self.session_context:
            base["session_context"] = self.session_context
        if self.code_context:
            base["code_context"] = self.code_context
        if self.design_patterns:
            base["design_patterns"] = self.design_patterns
        if self.problem_solving_approach:
            base["problem_solving_approach"] = self.problem_solving_approach

        return base


class PatternDetector:
    """Enhanced pattern detector with v2 capabilities."""

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

    def __init__(
        self,
        store: EventStore,
        enable_v2: bool = True,
        project_path: Optional[Path] = None,
    ):
        """
        Initialize pattern detector.

        Args:
            store: EventStore instance
            enable_v2: Enable v2 enhancements (session analysis, LSP, design patterns)
            project_path: Optional project path for LSP analysis
        """
        self.store = store
        self.enable_v2 = enable_v2 and V2_AVAILABLE
        self.project_path = project_path

        # V2 analyzers (initialized on demand)
        self._session_analyzer = None
        self._lsp_analyzer = None
        self._design_pattern_detector = None

    @property
    def session_analyzer(self) -> Optional["SessionAnalyzer"]:
        """Lazy-load session analyzer."""
        if self.enable_v2 and self._session_analyzer is None and V2_AVAILABLE:
            self._session_analyzer = SessionAnalyzer(self.store)
        return self._session_analyzer

    @property
    def lsp_analyzer(self) -> Optional["LSPAnalyzer"]:
        """Lazy-load LSP analyzer."""
        if self.enable_v2 and self._lsp_analyzer is None and V2_AVAILABLE:
            self._lsp_analyzer = LSPAnalyzer()
        return self._lsp_analyzer

    @property
    def design_pattern_detector(self) -> Optional["DesignPatternDetector"]:
        """Lazy-load design pattern detector."""
        if self.enable_v2 and self._design_pattern_detector is None and V2_AVAILABLE:
            self._design_pattern_detector = DesignPatternDetector(self.lsp_analyzer)
        return self._design_pattern_detector

    def detect_patterns(
        self,
        project_path: Optional[str] = None,
        min_occurrences: int = 3,
        min_sequence_length: int = 2,
        max_sequence_length: int = 10,
        lookback_days: int = 7,
    ) -> list[DetectedPattern]:
        """
        Detect workflow patterns with v1 + v2 analysis.

        Returns patterns sorted by confidence.
        """
        # V1: Get tool sequences and find patterns
        sequences = self.store.get_tool_sequences(
            project_path=project_path,
            lookback_days=lookback_days,
            min_sequence_length=min_sequence_length,
        )

        if not sequences:
            return []

        matcher = SequenceMatcher(
            min_length=min_sequence_length,
            max_length=max_sequence_length,
            min_occurrences=min_occurrences,
        )

        matches = matcher.find_common_subsequences(sequences)

        if not matches:
            return []

        # Get full event data
        event_sessions = self.store.get_events_with_inputs(
            project_path=project_path,
            lookback_days=lookback_days,
        )

        # Convert matches to DetectedPatterns
        patterns = []
        for match in matches:
            pattern = self._create_pattern(match, event_sessions, project_path)
            if pattern:
                patterns.append(pattern)

        # Sort by confidence
        patterns.sort(key=lambda p: -p.confidence)

        return patterns

    def _create_pattern(
        self,
        match: SequenceMatch,
        event_sessions: list[list[ToolEvent]],
        project_path: Optional[str] = None,
    ) -> Optional[DetectedPattern]:
        """Create DetectedPattern with v1 + v2 metadata."""
        if not match.session_indices:
            return None

        # V1: Collect basic metadata
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

        # V1: Calculate confidence
        confidence = self._calculate_confidence(
            occurrence_count=match.occurrences,
            sequence_length=match.length,
            success_rate=success_rate,
            first_seen=first_seen,
            last_seen=last_seen,
        )

        # V1: Generate name and description
        suggested_name = self._generate_name(list(match.sequence))
        suggested_description = self._generate_description(list(match.sequence))

        # Create base pattern
        pattern = DetectedPattern(
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

        # V2: Add enhanced analysis
        if self.enable_v2:
            pattern = self._enhance_with_v2(pattern, session_ids, project_path)

        return pattern

    def _enhance_with_v2(
        self,
        pattern: DetectedPattern,
        session_ids: list[str],
        project_path: Optional[str],
    ) -> DetectedPattern:
        """Enhance pattern with v2 analysis."""
        # Session context analysis
        if self.session_analyzer:
            pattern.session_context = self._analyze_session_context(session_ids)

        # Code structure analysis
        if self.lsp_analyzer and project_path:
            pattern.code_context = self._analyze_code_context(Path(project_path))

        # Design pattern detection
        if self.design_pattern_detector:
            pattern.design_patterns = self._detect_design_patterns(
                pattern.tool_sequence, pattern.session_context, project_path
            )

        # Problem-solving approach
        if pattern.session_context and pattern.session_context.get("workflow_type"):
            pattern.problem_solving_approach = self._create_problem_solving_approach(
                pattern.session_context["workflow_type"]
            )

        return pattern

    def _analyze_session_context(self, session_ids: list[str]) -> dict:
        """Analyze session context across multiple sessions."""
        if not self.session_analyzer:
            return {}

        # Analyze first few sessions (sample)
        contexts = []
        for session_id in session_ids[:5]:
            ctx = self.session_analyzer.analyze_session(session_id)
            contexts.append(ctx)

        if not contexts:
            return {}

        # Aggregate insights
        primary_intents = [ctx.primary_intent for ctx in contexts if ctx.primary_intent]
        problem_domains = []
        for ctx in contexts:
            problem_domains.extend(ctx.problem_domains)
        workflow_types = [ctx.workflow_type for ctx in contexts if ctx.workflow_type]

        # Calculate aggregates
        avg_tool_success = sum(
            ctx.success_indicators.get("tool_success_rate", 0) for ctx in contexts
        ) / len(contexts)

        avg_duration = sum(
            ctx.success_indicators.get("session_duration_minutes", 0) for ctx in contexts
        ) / len(contexts)

        return {
            "primary_intent": max(set(primary_intents), key=primary_intents.count)
            if primary_intents
            else None,
            "problem_domains": list(set(problem_domains))[:5],
            "workflow_type": max(set(workflow_types), key=workflow_types.count)
            if workflow_types
            else None,
            "tool_success_rate": round(avg_tool_success, 2),
            "avg_session_duration_minutes": round(avg_duration, 1),
        }

    def _analyze_code_context(self, project_path: Path) -> dict:
        """Analyze code structure for the project."""
        if not self.lsp_analyzer or not project_path.exists():
            return {}

        try:
            structure = self.lsp_analyzer.analyze_project(project_path)

            # Extract key symbols (classes and functions)
            classes = self.lsp_analyzer.find_symbols_by_type(structure, "class")
            functions = self.lsp_analyzer.find_symbols_by_type(structure, "function")

            return {
                "analyzed_files": len(set(s.file_path for s in structure.symbols)),
                "primary_languages": ["python"],  # Could be detected from extensions
                "detected_symbols": {
                    "classes": [
                        {
                            "name": cls.name,
                            "file": str(cls.file_path.relative_to(project_path)),
                            "line": cls.line_number,
                        }
                        for cls in classes[:10]
                    ],
                    "functions": [
                        {
                            "name": func.name,
                            "file": str(func.file_path.relative_to(project_path)),
                            "line": func.line_number,
                        }
                        for func in functions[:10]
                    ],
                },
                "dependencies": [
                    {
                        "source": dep.source,
                        "target": dep.target,
                        "type": dep.import_type,
                    }
                    for dep in structure.dependencies[:10]
                ],
            }
        except Exception as e:
            print(f"Warning: LSP analysis failed: {e}")
            return {}

    def _detect_design_patterns(
        self,
        tool_sequence: list[str],
        session_context: Optional[dict],
        project_path: Optional[str],
    ) -> list[dict]:
        """Detect design patterns from workflow and code."""
        if not self.design_pattern_detector:
            return []

        patterns = []

        # Workflow pattern from tool sequence
        workflow_pattern = self.design_pattern_detector.detect_workflow_pattern(
            tool_sequence, session_context
        )
        if workflow_pattern:
            patterns.append(
                {
                    "name": workflow_pattern.pattern_name,
                    "type": workflow_pattern.pattern_type,
                    "confidence": round(workflow_pattern.confidence, 2),
                    "description": workflow_pattern.description,
                    "indicators": workflow_pattern.indicators[:5],
                }
            )

        # Code patterns from project (if available)
        if project_path and Path(project_path).exists():
            try:
                code_patterns = self.design_pattern_detector.detect_patterns_in_project(
                    Path(project_path)
                )
                for cp in code_patterns[:3]:  # Top 3 code patterns
                    patterns.append(
                        {
                            "name": cp.pattern_name,
                            "type": cp.pattern_type,
                            "confidence": round(cp.confidence, 2),
                            "description": cp.description,
                            "indicators": cp.indicators[:5],
                        }
                    )
            except Exception as e:
                print(f"Warning: Code pattern detection failed: {e}")

        return patterns

    def _create_problem_solving_approach(self, workflow_type: str) -> dict:
        """Create problem-solving approach metadata."""
        approaches = {
            "TDD": {
                "type": "TDD",
                "description": "Test-Driven Development workflow",
                "when_to_use": "When building new features or fixing bugs with test coverage",
                "steps": [
                    "Write a failing test that defines desired behavior",
                    "Run tests to confirm the failure (Red)",
                    "Write minimal code to make the test pass (Green)",
                    "Run tests to confirm they pass",
                    "Refactor code while keeping tests green",
                ],
                "benefits": [
                    "Better test coverage",
                    "Forces thinking about requirements first",
                    "Confidence when refactoring",
                ],
                "trade_offs": [
                    "Slower initial development",
                    "Requires discipline to follow the cycle",
                ],
            },
            "Refactor-Safe": {
                "type": "Refactor-Safe",
                "description": "Safe refactoring with continuous testing",
                "when_to_use": "When improving code structure without changing behavior",
                "steps": [
                    "Read and understand the current implementation",
                    "Identify code smells and refactoring opportunities",
                    "Make small, incremental changes",
                    "Run tests after each change to ensure behavior preservation",
                    "Commit working state before next refactor",
                ],
                "benefits": [
                    "Maintains test coverage throughout",
                    "Reduces risk of introducing bugs",
                    "Clear rollback points",
                ],
                "trade_offs": [
                    "Slower than rewriting from scratch",
                    "Requires good test coverage to be safe",
                ],
            },
            "Debug-Systematic": {
                "type": "Debug-Systematic",
                "description": "Systematic debugging approach",
                "when_to_use": "When tracking down bugs or unexpected behavior",
                "steps": [
                    "Read code to understand the flow",
                    "Search for error messages or suspicious patterns",
                    "Add logging or debugging statements",
                    "Run code to observe behavior",
                    "Form hypothesis and test it",
                    "Fix the issue and verify",
                ],
                "benefits": [
                    "Structured approach reduces frustration",
                    "Learns about codebase during debugging",
                    "Verifiable fix",
                ],
                "trade_offs": ["Can be time-consuming for complex issues"],
            },
        }

        return approaches.get(workflow_type, {
            "type": workflow_type,
            "description": f"Detected workflow pattern: {workflow_type}",
        })

    # V1 Helper Methods (unchanged)

    def _find_sequence_in_session(
        self, sequence: tuple[str, ...], events: list[ToolEvent]
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
        """Calculate confidence score for a pattern."""
        occurrence_score = min(1.0, math.log(occurrence_count + 1) / math.log(10))

        if 3 <= sequence_length <= 5:
            length_score = 1.0
        elif sequence_length == 2:
            length_score = 0.7
        elif sequence_length > 5:
            length_score = max(0.5, 1.0 - (sequence_length - 5) * 0.1)
        else:
            length_score = 0.5

        success_score = success_rate

        days_since_last = (datetime.now(timezone.utc) - last_seen).days
        recency_score = max(0.5, 1.0 - days_since_last * 0.05)

        confidence = (
            occurrence_score * 0.4
            + length_score * 0.2
            + success_score * 0.25
            + recency_score * 0.15
        )

        return min(1.0, max(0.0, confidence))

    def _generate_pattern_id(self, sequence: tuple[str, ...]) -> str:
        """Generate unique ID for a pattern."""
        seq_str = "-".join(sequence)
        return hashlib.sha256(seq_str.encode()).hexdigest()[:12]

    def _generate_name(self, tools: list[str]) -> str:
        """Generate human-readable name for a pattern."""
        if not tools:
            return "unknown-workflow"

        first_verb = self.TOOL_VERBS.get(tools[0], tools[0].lower())
        last_verb = self.TOOL_VERBS.get(tools[-1], tools[-1].lower())

        if len(tools) == 2:
            return f"{first_verb}-then-{last_verb}"
        else:
            return f"{first_verb}-and-{last_verb}"

    def _generate_description(self, tools: list[str]) -> str:
        """Generate description for a pattern."""
        if not tools:
            return "Unknown workflow pattern"
        tool_list = ", ".join(tools)
        return f"Workflow pattern: {tool_list}"

    def get_pending_patterns(
        self, project_path: Optional[str] = None, min_confidence: float = 0.7
    ) -> list[DetectedPattern]:
        """Get patterns that haven't been converted to skills yet."""
        patterns = self.detect_patterns(project_path=project_path)
        return [p for p in patterns if p.confidence >= min_confidence]
