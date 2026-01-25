"""Tests for the PatternDetector module."""

import tempfile
import pytest
from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.event_store import EventStore
from core.pattern_detector import PatternDetector, DetectedPattern


class TestPatternDetector:
    """Tests for PatternDetector class."""

    @pytest.fixture
    def store(self, tmp_path):
        """Create a temporary EventStore."""
        db_path = tmp_path / "test_events.db"
        return EventStore(db_path=db_path)

    @pytest.fixture
    def detector(self, store):
        """Create a PatternDetector with the test store."""
        return PatternDetector(store)

    def test_detect_patterns_empty(self, detector):
        """Test detection with no events."""
        patterns = detector.detect_patterns()
        assert patterns == []

    def test_detect_patterns_basic(self, store, detector):
        """Test basic pattern detection."""
        # Create repeated sequences across sessions
        for session_id in ["s1", "s2", "s3"]:
            for tool in ["Grep", "Read", "Edit"]:
                store.record_event(
                    session_id=session_id,
                    project_path="/test",
                    tool_name=tool,
                    tool_input={},
                )

        patterns = detector.detect_patterns(min_occurrences=3)

        assert len(patterns) >= 1
        # Should detect the Grep -> Read -> Edit pattern
        pattern = patterns[0]
        assert pattern.occurrence_count >= 3
        assert len(pattern.tool_sequence) >= 2

    def test_detect_patterns_project_filter(self, store, detector):
        """Test filtering patterns by project."""
        # Project A: specific pattern
        for session in ["a1", "a2", "a3"]:
            for tool in ["Read", "Write"]:
                store.record_event(
                    session_id=session,
                    project_path="/project-a",
                    tool_name=tool,
                    tool_input={},
                )

        # Project B: different pattern
        for session in ["b1", "b2", "b3"]:
            for tool in ["Grep", "Bash"]:
                store.record_event(
                    session_id=session,
                    project_path="/project-b",
                    tool_name=tool,
                    tool_input={},
                )

        patterns_a = detector.detect_patterns(project_path="/project-a")
        patterns_b = detector.detect_patterns(project_path="/project-b")

        # Each project should have its own patterns
        assert len(patterns_a) >= 1
        assert len(patterns_b) >= 1

        # Patterns should be different
        if patterns_a and patterns_b:
            assert patterns_a[0].tool_sequence != patterns_b[0].tool_sequence

    def test_confidence_calculation(self, detector):
        """Test confidence score calculation."""
        # High occurrence, good length, high success
        high_conf = detector._calculate_confidence(
            occurrence_count=10,
            sequence_length=4,
            success_rate=1.0,
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
        )

        # Low occurrence, short length
        low_conf = detector._calculate_confidence(
            occurrence_count=3,
            sequence_length=2,
            success_rate=0.5,
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
        )

        assert high_conf > low_conf
        assert 0 <= high_conf <= 1
        assert 0 <= low_conf <= 1

    def test_generate_name(self, detector):
        """Test pattern name generation."""
        name = detector._generate_name(["Read", "Edit", "Bash"])
        assert "read" in name.lower() or "bash" in name.lower()

        name2 = detector._generate_name(["Grep", "Write"])
        assert "search" in name2.lower() or "write" in name2.lower()

    def test_generate_description(self, detector):
        """Test pattern description generation."""
        desc = detector._generate_description(["Read", "Edit", "Write"])
        assert "Workflow" in desc or "workflow" in desc

    def test_pattern_id_unique(self, detector):
        """Test that pattern IDs are unique for different sequences."""
        id1 = detector._generate_pattern_id(("Read", "Edit"))
        id2 = detector._generate_pattern_id(("Edit", "Read"))
        id3 = detector._generate_pattern_id(("Read", "Edit"))

        assert id1 != id2  # Different sequences = different IDs
        assert id1 == id3  # Same sequence = same ID


class TestDetectedPattern:
    """Tests for DetectedPattern dataclass."""

    def test_to_dict(self):
        """Test serialization to dictionary."""
        pattern = DetectedPattern(
            id="test-123",
            tool_sequence=["Read", "Edit"],
            occurrence_count=5,
            confidence=0.85,
            session_ids=["s1", "s2"],
            first_seen=datetime(2024, 1, 1),
            last_seen=datetime(2024, 1, 15),
            success_rate=0.9,
            suggested_name="read-and-edit",
            suggested_description="A workflow pattern",
        )

        data = pattern.to_dict()

        assert data["id"] == "test-123"
        assert data["tool_sequence"] == ["Read", "Edit"]
        assert data["confidence"] == 0.85
        assert data["occurrence_count"] == 5
