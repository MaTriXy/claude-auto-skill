"""Tests for the EventStore module."""

import tempfile
import pytest
from datetime import datetime, timedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.event_store import EventStore, ToolEvent


class TestEventStore:
    """Tests for EventStore class."""

    @pytest.fixture
    def store(self, tmp_path):
        """Create a temporary EventStore for testing."""
        db_path = tmp_path / "test_events.db"
        return EventStore(db_path=db_path)

    def test_record_event(self, store):
        """Test recording a basic event."""
        event = store.record_event(
            session_id="test-session-1",
            project_path="/test/project",
            tool_name="Read",
            tool_input={"file_path": "/test/file.py"},
            tool_response="file contents here",
            success=True,
        )

        assert event.session_id == "test-session-1"
        assert event.project_path == "/test/project"
        assert event.tool_name == "Read"
        assert event.tool_input == {"file_path": "/test/file.py"}
        assert event.success is True

    def test_get_session_events(self, store):
        """Test retrieving events for a session."""
        # Record multiple events
        store.record_event(
            session_id="session-1",
            project_path="/test",
            tool_name="Read",
            tool_input={},
        )
        store.record_event(
            session_id="session-1",
            project_path="/test",
            tool_name="Edit",
            tool_input={},
        )
        store.record_event(
            session_id="session-2",
            project_path="/test",
            tool_name="Write",
            tool_input={},
        )

        events = store.get_session_events("session-1")
        assert len(events) == 2
        assert events[0].tool_name == "Read"
        assert events[1].tool_name == "Edit"

    def test_get_tool_sequences(self, store):
        """Test extracting tool sequences from sessions."""
        # Create two sessions with similar sequences
        for session_id in ["s1", "s2", "s3"]:
            for tool in ["Grep", "Read", "Edit"]:
                store.record_event(
                    session_id=session_id,
                    project_path="/test",
                    tool_name=tool,
                    tool_input={},
                )

        sequences = store.get_tool_sequences(min_sequence_length=2)
        assert len(sequences) == 3
        assert sequences[0] == ["Grep", "Read", "Edit"]

    def test_get_tool_sequences_project_filter(self, store):
        """Test filtering sequences by project."""
        # Project A sessions
        for session_id in ["a1", "a2", "a3"]:
            for tool in ["Read", "Write"]:
                store.record_event(
                    session_id=session_id,
                    project_path="/project-a",
                    tool_name=tool,
                    tool_input={},
                )

        # Project B session
        store.record_event(
            session_id="b1",
            project_path="/project-b",
            tool_name="Bash",
            tool_input={},
        )

        sequences_a = store.get_tool_sequences(project_path="/project-a")
        sequences_b = store.get_tool_sequences(project_path="/project-b")

        assert len(sequences_a) == 3
        assert len(sequences_b) == 0  # Single tool doesn't meet min_sequence_length

    def test_truncate_response(self, store):
        """Test that large responses are truncated."""
        long_response = "x" * 2000
        event = store.record_event(
            session_id="test",
            project_path="/test",
            tool_name="Read",
            tool_input={},
            tool_response=long_response,
        )

        # Response should be truncated
        assert len(event.tool_response) < len(long_response)
        assert event.tool_response.endswith("...[truncated]")

    def test_get_stats(self, store):
        """Test statistics calculation."""
        # Record some events
        for i in range(5):
            store.record_event(
                session_id=f"session-{i % 2}",
                project_path=f"/project-{i % 3}",
                tool_name="Read" if i % 2 == 0 else "Write",
                tool_input={},
            )

        stats = store.get_stats()
        assert stats["total_events"] == 5
        assert stats["unique_sessions"] == 2
        assert stats["unique_projects"] == 3
        assert len(stats["top_tools"]) > 0

    def test_cleanup_old_events(self, store):
        """Test cleanup of old events."""
        # This test would need to manipulate timestamps directly
        # For now, just verify the method runs without error
        deleted = store.cleanup_old_events(days=30)
        assert deleted == 0  # No old events to delete


class TestToolEvent:
    """Tests for ToolEvent dataclass."""

    def test_to_dict(self):
        """Test serialization to dictionary."""
        event = ToolEvent(
            id="test-id",
            session_id="session-1",
            project_path="/test",
            tool_name="Read",
            tool_input={"file": "test.py"},
            tool_response="contents",
            success=True,
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
        )

        data = event.to_dict()
        assert data["id"] == "test-id"
        assert data["tool_name"] == "Read"
        assert data["timestamp"] == "2024-01-15T10:30:00"
