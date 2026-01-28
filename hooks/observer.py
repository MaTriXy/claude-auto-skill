#!/usr/bin/env python3
"""
Observer Hook - Captures tool usage events and triggers pattern detection.

Called by Claude Code via PostToolUse and Stop hooks:
- PostToolUse: Records each tool invocation to the event store
- Stop: Triggers pattern detection and notifies user of findings
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.event_store import EventStore
from core.pattern_detector import PatternDetector
from core.skill_generator import SkillGenerator
from core.agent_registry import AgentRegistry


def get_session_id() -> str:
    """Get the current Claude session ID from environment."""
    return os.environ.get("CLAUDE_SESSION_ID", "unknown")


def get_project_path() -> str:
    """Get the current project path from environment."""
    return os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())


def get_agent_id() -> str:
    """Detect the current agent from environment."""
    registry = AgentRegistry()
    agent = registry.detect_current_agent()
    return agent.id if agent else "unknown"


def parse_hook_input() -> dict:
    """Parse the hook input from stdin (JSON format)."""
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            return {}
        return json.loads(input_data)
    except json.JSONDecodeError:
        return {}


def record_event() -> None:
    """
    Record a tool usage event (called by PostToolUse hook).

    Expects hook input with:
    - tool_name: Name of the tool that was called
    - tool_input: Input parameters to the tool
    - tool_response: Response from the tool
    """
    hook_input = parse_hook_input()

    tool_name = hook_input.get("tool_name")
    if not tool_name:
        # No tool info provided, skip
        return

    # Skip recording our own hooks to avoid recursion
    if "auto-skill" in tool_name.lower():
        return

    store = EventStore()

    # Validate and extract tool_input
    tool_input = hook_input.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}

    # Determine success from response (simple heuristic)
    tool_response = hook_input.get("tool_response", "")
    success = not any(
        err in str(tool_response).lower()
        for err in ["error", "failed", "exception", "traceback"]
    )

    store.record_event(
        session_id=get_session_id(),
        project_path=get_project_path(),
        tool_name=tool_name,
        tool_input=tool_input,
        tool_response=str(tool_response) if tool_response else None,
        success=success,
        agent_id=get_agent_id(),
    )


def analyze_session() -> None:
    """
    Analyze the current session for patterns (called by Stop hook).

    Checks for repeated tool sequences and suggests skill candidates.
    """
    store = EventStore()
    detector = PatternDetector(store)

    # Get current session events
    session_id = get_session_id()
    project_path = get_project_path()

    # Detect patterns across all sessions for this project
    patterns = detector.detect_patterns(
        project_path=project_path,
        min_occurrences=3,
        min_sequence_length=2,
        max_sequence_length=10,
    )

    if not patterns:
        return

    # Filter to high-confidence patterns
    high_confidence = [p for p in patterns if p.confidence >= 0.7]

    if not high_confidence:
        return

    # Output notification for user
    print("\n" + "=" * 60)
    print("Auto-Skill: Detected workflow patterns!")
    print("=" * 60)

    for pattern in high_confidence[:3]:  # Show top 3
        print(f"\nPattern: {' -> '.join(pattern.tool_sequence)}")
        print(f"  Occurrences: {pattern.occurrence_count}")
        print(f"  Confidence: {pattern.confidence:.0%}")

    print("\nRun /auto-skill:review to review and approve skill candidates.")
    print("=" * 60 + "\n")


def main() -> None:
    """Main entry point for the hook."""
    if len(sys.argv) < 2:
        print("Usage: observer.py <record|analyze>", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    if command == "record":
        record_event()
    elif command == "analyze":
        analyze_session()
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
