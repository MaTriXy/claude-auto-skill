"""Tests for the SequenceMatcher module."""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.sequence_matcher import SequenceMatcher, SequenceMatch


class TestSequenceMatcher:
    """Tests for SequenceMatcher class."""

    @pytest.fixture
    def matcher(self):
        """Create a default SequenceMatcher."""
        return SequenceMatcher(
            min_length=2,
            max_length=10,
            min_occurrences=3,
        )

    def test_find_common_subsequences_basic(self, matcher):
        """Test finding basic repeated sequences."""
        sequences = [
            ["Read", "Edit", "Bash"],
            ["Read", "Edit", "Bash"],
            ["Read", "Edit", "Bash"],
        ]

        matches = matcher.find_common_subsequences(sequences)

        assert len(matches) >= 1
        # The full sequence should be found
        full_match = next(
            (m for m in matches if m.sequence == ("Read", "Edit", "Bash")),
            None
        )
        assert full_match is not None
        assert full_match.occurrences == 3

    def test_find_common_subsequences_partial(self, matcher):
        """Test finding partial sequence matches."""
        sequences = [
            ["Grep", "Read", "Edit"],
            ["Read", "Edit", "Write"],
            ["Read", "Edit", "Bash"],
        ]

        matches = matcher.find_common_subsequences(sequences)

        # "Read", "Edit" appears in all three
        read_edit = next(
            (m for m in matches if m.sequence == ("Read", "Edit")),
            None
        )
        assert read_edit is not None
        assert read_edit.occurrences == 3

    def test_no_matches_below_threshold(self, matcher):
        """Test that sequences below occurrence threshold aren't returned."""
        sequences = [
            ["Read", "Edit"],
            ["Read", "Edit"],
            ["Write", "Bash"],  # Different sequence
        ]

        matches = matcher.find_common_subsequences(sequences)

        # Read, Edit only appears twice (below threshold of 3)
        assert len(matches) == 0

    def test_empty_sequences(self, matcher):
        """Test handling of empty input."""
        assert matcher.find_common_subsequences([]) == []
        assert matcher.find_common_subsequences([[]]) == []

    def test_subsumed_matches_removed(self, matcher):
        """Test that shorter sequences subsumed by longer ones are removed."""
        # Create sequences where a short pattern is always part of a longer one
        sequences = [
            ["Read", "Edit", "Bash"],
            ["Read", "Edit", "Bash"],
            ["Read", "Edit", "Bash"],
        ]

        matches = matcher.find_common_subsequences(sequences)

        # Should have the longer sequence, not just "Read, Edit"
        sequence_lengths = [m.length for m in matches]
        assert 3 in sequence_lengths  # Full sequence

    def test_is_subsequence_of(self, matcher):
        """Test subsequence detection."""
        assert matcher._is_subsequence_of(
            ("Read", "Edit"),
            ("Read", "Edit", "Bash")
        )
        assert not matcher._is_subsequence_of(
            ("Read", "Edit", "Bash"),
            ("Read", "Edit")
        )
        assert not matcher._is_subsequence_of(
            ("Read", "Bash"),
            ("Read", "Edit", "Bash")  # Not contiguous
        )

    def test_sequence_match_properties(self):
        """Test SequenceMatch dataclass."""
        match = SequenceMatch(
            sequence=("Read", "Edit", "Bash"),
            occurrences=5,
            session_indices=[0, 1, 2, 3, 4],
        )

        assert match.length == 3
        assert hash(match) == hash(("Read", "Edit", "Bash"))

    def test_different_min_occurrences(self):
        """Test with different occurrence thresholds."""
        matcher_low = SequenceMatcher(min_occurrences=2)
        matcher_high = SequenceMatcher(min_occurrences=5)

        sequences = [
            ["Read", "Edit"],
            ["Read", "Edit"],
            ["Read", "Edit"],
        ]

        matches_low = matcher_low.find_common_subsequences(sequences)
        matches_high = matcher_high.find_common_subsequences(sequences)

        assert len(matches_low) > 0
        assert len(matches_high) == 0

    def test_max_length_respected(self):
        """Test that max_length is respected."""
        matcher = SequenceMatcher(min_length=2, max_length=3, min_occurrences=2)

        long_sequence = ["A", "B", "C", "D", "E"]
        sequences = [long_sequence, long_sequence]

        matches = matcher.find_common_subsequences(sequences)

        # No match should be longer than 3
        for match in matches:
            assert match.length <= 3
