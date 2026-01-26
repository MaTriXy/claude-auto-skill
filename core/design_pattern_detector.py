"""
Design Pattern Detector - Identifies architectural and coding patterns.

Detects patterns at multiple levels:
- Architectural patterns (MVC, Repository, Factory, Singleton, etc.)
- Coding patterns (error handling, API design, data flow)
- Workflow patterns (TDD, refactoring approaches, debugging strategies)
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .lsp_analyzer import CodeStructure, CodeSymbol, LSPAnalyzer


@dataclass
class DesignPattern:
    """Represents a detected design pattern."""

    pattern_id: str
    pattern_type: str  # "architectural", "coding", "workflow"
    pattern_name: str  # e.g., "MVC", "Factory", "Error-First-Handling"
    confidence: float  # 0.0 to 1.0
    description: str
    indicators: list[str]  # What led to detection
    affected_files: list[Path] = field(default_factory=list)
    code_examples: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class PatternContext:
    """Context about when/why a pattern is appropriate."""

    pattern_name: str
    when_to_use: str
    benefits: list[str]
    trade_offs: list[str]
    common_mistakes: list[str] = field(default_factory=list)


class DesignPatternDetector:
    """Detects design patterns in code and workflows."""

    # Architectural patterns and their indicators
    ARCHITECTURAL_PATTERNS = {
        "MVC": {
            "indicators": [
                "model",
                "view",
                "controller",
                "models/",
                "views/",
                "controllers/",
            ],
            "description": "Model-View-Controller separation pattern",
            "min_confidence": 0.6,
        },
        "Repository": {
            "indicators": ["repository", "repo", "data_access", "dal"],
            "description": "Repository pattern for data access abstraction",
            "min_confidence": 0.5,
        },
        "Factory": {
            "indicators": ["factory", "create_", "builder"],
            "description": "Factory pattern for object creation",
            "min_confidence": 0.5,
        },
        "Singleton": {
            "indicators": ["singleton", "_instance", "get_instance"],
            "description": "Singleton pattern for single-instance classes",
            "min_confidence": 0.6,
        },
        "Strategy": {
            "indicators": ["strategy", "algorithm", "policy"],
            "description": "Strategy pattern for interchangeable algorithms",
            "min_confidence": 0.5,
        },
        "Observer": {
            "indicators": ["observer", "subscriber", "listener", "event"],
            "description": "Observer pattern for event handling",
            "min_confidence": 0.5,
        },
        "Adapter": {
            "indicators": ["adapter", "wrapper", "facade"],
            "description": "Adapter pattern for interface compatibility",
            "min_confidence": 0.5,
        },
        "Dependency-Injection": {
            "indicators": ["inject", "container", "provider", "di_"],
            "description": "Dependency Injection pattern",
            "min_confidence": 0.6,
        },
    }

    # Coding patterns (lower-level code organization)
    CODING_PATTERNS = {
        "Error-First-Handling": {
            "indicators": ["try", "except", "raise", "error", "exception"],
            "description": "Error-first error handling pattern",
            "min_confidence": 0.4,
        },
        "REST-API-Design": {
            "indicators": ["@app.route", "@router", "GET", "POST", "PUT", "DELETE"],
            "description": "RESTful API design pattern",
            "min_confidence": 0.5,
        },
        "Async-Pattern": {
            "indicators": ["async", "await", "asyncio", "concurrent"],
            "description": "Asynchronous programming pattern",
            "min_confidence": 0.5,
        },
        "Decorator-Pattern": {
            "indicators": ["@decorator", "@property", "@staticmethod"],
            "description": "Python decorator pattern",
            "min_confidence": 0.4,
        },
        "Context-Manager": {
            "indicators": ["__enter__", "__exit__", "with ", "contextmanager"],
            "description": "Context manager pattern (with statement)",
            "min_confidence": 0.5,
        },
        "Builder-Pattern": {
            "indicators": ["builder", "build()", "with_", "set_"],
            "description": "Fluent builder pattern",
            "min_confidence": 0.5,
        },
    }

    # Workflow patterns (from session analysis)
    WORKFLOW_PATTERNS = {
        "TDD": {
            "tool_sequence": ["Write", "Bash", "Edit", "Bash"],
            "description": "Test-Driven Development workflow",
            "indicators": ["test", "assert", "pytest", "unittest"],
        },
        "Refactor-Safe": {
            "tool_sequence": ["Read", "Edit", "Bash"],
            "description": "Safe refactoring with tests",
            "indicators": ["refactor", "test", "extract", "rename"],
        },
        "Debug-Systematic": {
            "tool_sequence": ["Read", "Grep", "Bash", "Edit"],
            "description": "Systematic debugging approach",
            "indicators": ["debug", "print", "log", "trace"],
        },
        "Explore-Then-Implement": {
            "tool_sequence": ["Grep", "Read", "Read", "Write"],
            "description": "Exploration before implementation",
            "indicators": ["understand", "explore", "analyze"],
        },
    }

    def __init__(self, lsp_analyzer: Optional[LSPAnalyzer] = None):
        """
        Initialize design pattern detector.

        Args:
            lsp_analyzer: Optional LSPAnalyzer for code structure analysis
        """
        self.lsp_analyzer = lsp_analyzer or LSPAnalyzer()

    def detect_patterns_in_project(
        self, project_path: Path, language: str = "python"
    ) -> list[DesignPattern]:
        """
        Detect all design patterns in a project.

        Args:
            project_path: Root path of the project
            language: Programming language

        Returns:
            List of detected design patterns
        """
        # Analyze code structure
        structure = self.lsp_analyzer.analyze_project(project_path, language)

        # Detect architectural patterns
        arch_patterns = self._detect_architectural_patterns(structure)

        # Detect coding patterns
        code_patterns = self._detect_coding_patterns(structure)

        # Combine all patterns
        all_patterns = arch_patterns + code_patterns

        # Sort by confidence
        return sorted(all_patterns, key=lambda p: -p.confidence)

    def detect_workflow_pattern(
        self, tool_sequence: list[str], session_context: Optional[dict] = None
    ) -> Optional[DesignPattern]:
        """
        Detect workflow pattern from tool usage sequence.

        Args:
            tool_sequence: Sequence of tool names used
            session_context: Optional context from session analyzer

        Returns:
            Detected workflow pattern or None
        """
        for pattern_name, pattern_info in self.WORKFLOW_PATTERNS.items():
            expected_seq = pattern_info["tool_sequence"]

            # Check if expected sequence appears in tool sequence
            if self._contains_subsequence(tool_sequence, expected_seq):
                # Check for supporting indicators in context
                confidence = 0.7  # Base confidence for sequence match

                if session_context:
                    # Boost confidence if context indicators match
                    indicators = pattern_info.get("indicators", [])
                    context_text = str(session_context).lower()
                    matching_indicators = [
                        ind for ind in indicators if ind in context_text
                    ]

                    if matching_indicators:
                        confidence = min(0.95, confidence + 0.05 * len(matching_indicators))

                return DesignPattern(
                    pattern_id=f"workflow-{pattern_name.lower()}",
                    pattern_type="workflow",
                    pattern_name=pattern_name,
                    confidence=confidence,
                    description=pattern_info["description"],
                    indicators=[f"Tool sequence: {' -> '.join(expected_seq)}"],
                    metadata={"tool_sequence": tool_sequence},
                )

        return None

    def _detect_architectural_patterns(
        self, structure: CodeStructure
    ) -> list[DesignPattern]:
        """Detect architectural patterns in code structure."""
        patterns = []

        for pattern_name, pattern_info in self.ARCHITECTURAL_PATTERNS.items():
            indicators_found = []
            affected_files = []

            # Check file/directory names
            for module in structure.modules:
                module_lower = module.lower()
                for indicator in pattern_info["indicators"]:
                    if indicator in module_lower:
                        indicators_found.append(f"Module: {module}")

            # Check symbol names
            for symbol in structure.symbols:
                symbol_name_lower = symbol.name.lower()
                for indicator in pattern_info["indicators"]:
                    if indicator in symbol_name_lower:
                        indicators_found.append(f"Symbol: {symbol.name}")
                        affected_files.append(symbol.file_path)

            # Calculate confidence based on indicator matches
            if indicators_found:
                # Normalize confidence: more indicators = higher confidence
                confidence = min(
                    1.0, len(indicators_found) / (len(pattern_info["indicators"]) * 2)
                )

                if confidence >= pattern_info["min_confidence"]:
                    patterns.append(
                        DesignPattern(
                            pattern_id=f"arch-{pattern_name.lower()}",
                            pattern_type="architectural",
                            pattern_name=pattern_name,
                            confidence=confidence,
                            description=pattern_info["description"],
                            indicators=indicators_found[:10],  # Limit to top 10
                            affected_files=list(set(affected_files))[:10],
                        )
                    )

        return patterns

    def _detect_coding_patterns(
        self, structure: CodeStructure
    ) -> list[DesignPattern]:
        """Detect coding patterns in source code."""
        patterns = []

        # Read source files to check for coding patterns
        analyzed_files = {}
        for symbol in structure.symbols:
            if symbol.file_path not in analyzed_files:
                try:
                    source = symbol.file_path.read_text()
                    analyzed_files[symbol.file_path] = source
                except Exception:
                    continue

        # Check each coding pattern
        for pattern_name, pattern_info in self.CODING_PATTERNS.items():
            indicators_found = []
            affected_files = []
            code_examples = []

            for file_path, source in analyzed_files.items():
                source_lower = source.lower()
                for indicator in pattern_info["indicators"]:
                    if indicator.lower() in source_lower:
                        indicators_found.append(f"Found '{indicator}' in {file_path.name}")
                        affected_files.append(file_path)

                        # Extract code example
                        example = self._extract_code_example(source, indicator)
                        if example:
                            code_examples.append(example)

            # Calculate confidence
            if indicators_found:
                confidence = min(
                    1.0, len(indicators_found) / (len(pattern_info["indicators"]) * 3)
                )

                if confidence >= pattern_info["min_confidence"]:
                    patterns.append(
                        DesignPattern(
                            pattern_id=f"code-{pattern_name.lower()}",
                            pattern_type="coding",
                            pattern_name=pattern_name,
                            confidence=confidence,
                            description=pattern_info["description"],
                            indicators=indicators_found[:10],
                            affected_files=list(set(affected_files))[:10],
                            code_examples=code_examples[:3],
                        )
                    )

        return patterns

    def _extract_code_example(self, source: str, indicator: str, context_lines: int = 3) -> Optional[str]:
        """Extract a small code example showing the indicator."""
        lines = source.split("\n")

        for i, line in enumerate(lines):
            if indicator.lower() in line.lower():
                # Extract context around the match
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                example = "\n".join(lines[start:end])
                return example[:200]  # Limit length

        return None

    def _contains_subsequence(self, sequence: list, subsequence: list) -> bool:
        """Check if subsequence appears in sequence."""
        sub_len = len(subsequence)
        return any(
            sequence[i : i + sub_len] == subsequence
            for i in range(len(sequence) - sub_len + 1)
        )

    def get_pattern_context(self, pattern_name: str) -> Optional[PatternContext]:
        """
        Get contextual information about when to use a pattern.

        Args:
            pattern_name: Name of the pattern

        Returns:
            PatternContext with usage guidance
        """
        # Predefined contexts for common patterns
        contexts = {
            "MVC": PatternContext(
                pattern_name="MVC",
                when_to_use="Building web applications with clear separation of concerns",
                benefits=[
                    "Separates business logic from presentation",
                    "Easier to test and maintain",
                    "Multiple views can share same model",
                ],
                trade_offs=[
                    "Can be overkill for simple applications",
                    "More files and indirection",
                ],
                common_mistakes=[
                    "Putting business logic in controllers",
                    "Tight coupling between layers",
                ],
            ),
            "Repository": PatternContext(
                pattern_name="Repository",
                when_to_use="When you need to abstract data access layer",
                benefits=[
                    "Decouples business logic from data access",
                    "Easy to swap data sources",
                    "Centralized data access logic",
                ],
                trade_offs=["Additional abstraction layer", "Can be over-engineering"],
                common_mistakes=["Leaking data access concerns to business layer"],
            ),
            "TDD": PatternContext(
                pattern_name="TDD",
                when_to_use="When building new features or fixing bugs",
                benefits=[
                    "Better test coverage",
                    "Forces you to think about requirements",
                    "Refactoring confidence",
                ],
                trade_offs=["Slower initial development", "Requires discipline"],
                common_mistakes=[
                    "Testing implementation instead of behavior",
                    "Skipping refactor step",
                ],
            ),
        }

        return contexts.get(pattern_name)

    def suggest_patterns_for_context(
        self, intent: str, problem_domain: str
    ) -> list[tuple[str, float]]:
        """
        Suggest relevant patterns based on intent and domain.

        Args:
            intent: User intent (e.g., "implement", "refactor")
            problem_domain: Problem domain (e.g., "api", "database")

        Returns:
            List of (pattern_name, relevance_score) tuples
        """
        suggestions = []

        # Map intents to patterns
        intent_patterns = {
            "implement": ["Factory", "Builder-Pattern", "Strategy"],
            "refactor": ["Refactor-Safe", "Extract-Method"],
            "debug": ["Debug-Systematic", "Error-First-Handling"],
            "test": ["TDD", "Mock-Pattern"],
        }

        # Map domains to patterns
        domain_patterns = {
            "api": ["REST-API-Design", "Adapter", "Repository"],
            "database": ["Repository", "DAO"],
            "async": ["Async-Pattern", "Observer"],
            "web": ["MVC", "REST-API-Design"],
        }

        # Score patterns by relevance
        intent_lower = intent.lower()
        domain_lower = problem_domain.lower()

        for intent_key, patterns in intent_patterns.items():
            if intent_key in intent_lower:
                for pattern in patterns:
                    suggestions.append((pattern, 0.8))

        for domain_key, patterns in domain_patterns.items():
            if domain_key in domain_lower:
                for pattern in patterns:
                    suggestions.append((pattern, 0.7))

        # Deduplicate and sort by score
        unique_suggestions = {}
        for pattern, score in suggestions:
            if pattern not in unique_suggestions or unique_suggestions[pattern] < score:
                unique_suggestions[pattern] = score

        return sorted(unique_suggestions.items(), key=lambda x: -x[1])
