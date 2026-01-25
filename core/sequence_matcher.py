"""
Sequence Matcher - Finds repeated subsequences in tool sequences.

Uses a sliding window approach to identify common patterns across
multiple sessions. Prioritizes longer sequences and higher occurrence counts.
"""

from collections import Counter
from dataclasses import dataclass
from typing import Hashable


@dataclass
class SequenceMatch:
    """A matched subsequence with occurrence information."""

    sequence: tuple[str, ...]
    occurrences: int
    session_indices: list[int]  # Which sessions contained this sequence

    @property
    def length(self) -> int:
        return len(self.sequence)

    def __hash__(self) -> int:
        return hash(self.sequence)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SequenceMatch):
            return False
        return self.sequence == other.sequence


class SequenceMatcher:
    """Finds repeated subsequences across multiple tool sequences."""

    def __init__(
        self,
        min_length: int = 2,
        max_length: int = 10,
        min_occurrences: int = 3,
    ):
        """
        Initialize the sequence matcher.

        Args:
            min_length: Minimum subsequence length to detect
            max_length: Maximum subsequence length to detect
            min_occurrences: Minimum times a sequence must appear
        """
        self.min_length = min_length
        self.max_length = max_length
        self.min_occurrences = min_occurrences

    def find_common_subsequences(
        self,
        sequences: list[list[str]],
    ) -> list[SequenceMatch]:
        """
        Find common subsequences across multiple tool sequences.

        Args:
            sequences: List of tool name sequences (one per session)

        Returns:
            List of SequenceMatch objects, sorted by (length desc, occurrences desc)
        """
        if not sequences:
            return []

        # Extract all subsequences of valid lengths
        subsequence_locations: dict[tuple[str, ...], list[int]] = {}

        for session_idx, sequence in enumerate(sequences):
            seen_in_session: set[tuple[str, ...]] = set()

            for length in range(self.min_length, min(self.max_length + 1, len(sequence) + 1)):
                for start in range(len(sequence) - length + 1):
                    subseq = tuple(sequence[start : start + length])

                    # Only count once per session
                    if subseq not in seen_in_session:
                        seen_in_session.add(subseq)
                        if subseq not in subsequence_locations:
                            subsequence_locations[subseq] = []
                        subsequence_locations[subseq].append(session_idx)

        # Filter to sequences meeting minimum occurrence threshold
        matches = []
        for subseq, session_indices in subsequence_locations.items():
            if len(session_indices) >= self.min_occurrences:
                matches.append(
                    SequenceMatch(
                        sequence=subseq,
                        occurrences=len(session_indices),
                        session_indices=session_indices,
                    )
                )

        # Remove subsequences that are fully contained in longer matches
        matches = self._remove_subsumed_matches(matches)

        # Sort by length (desc) then occurrences (desc)
        matches.sort(key=lambda m: (-m.length, -m.occurrences))

        return matches

    def _remove_subsumed_matches(
        self,
        matches: list[SequenceMatch],
    ) -> list[SequenceMatch]:
        """
        Remove shorter sequences that are always part of longer ones.

        A shorter sequence is subsumed if:
        1. It appears in the same sessions as a longer sequence
        2. It is a contiguous subsequence of that longer sequence
        """
        if not matches:
            return []

        # Sort by length descending to process longer sequences first
        sorted_matches = sorted(matches, key=lambda m: -m.length)
        kept: list[SequenceMatch] = []

        for match in sorted_matches:
            is_subsumed = False

            for longer in kept:
                if self._is_subsequence_of(match.sequence, longer.sequence):
                    # Check if all occurrences are explained by the longer sequence
                    if set(match.session_indices) <= set(longer.session_indices):
                        is_subsumed = True
                        break

            if not is_subsumed:
                kept.append(match)

        return kept

    def _is_subsequence_of(
        self,
        shorter: tuple[str, ...],
        longer: tuple[str, ...],
    ) -> bool:
        """Check if shorter is a contiguous subsequence of longer."""
        if len(shorter) >= len(longer):
            return False

        shorter_str = "|||".join(shorter)
        longer_str = "|||".join(longer)
        return shorter_str in longer_str

    def find_pattern_variations(
        self,
        base_sequence: tuple[str, ...],
        sequences: list[list[str]],
        max_variations: int = 3,
    ) -> list[tuple[str, ...]]:
        """
        Find variations of a base sequence (e.g., with optional steps).

        This helps identify patterns that are similar but not identical,
        which could be combined into a single skill with optional steps.
        """
        variations: list[tuple[str, ...]] = []

        for sequence in sequences:
            # Look for sequences that start and end the same but differ in middle
            if len(sequence) < len(base_sequence):
                continue

            for start in range(len(sequence) - len(base_sequence) + 1):
                # Check if this window matches the pattern with possible insertions
                candidate = tuple(sequence[start : start + len(base_sequence) + 2])
                if self._is_variation_of(base_sequence, candidate):
                    if candidate not in variations:
                        variations.append(candidate)
                        if len(variations) >= max_variations:
                            return variations

        return variations

    def _is_variation_of(
        self,
        base: tuple[str, ...],
        candidate: tuple[str, ...],
    ) -> bool:
        """
        Check if candidate is a variation of base.

        A variation has the same start and end but may have 1-2 extra steps.
        """
        if len(candidate) <= len(base) or len(candidate) > len(base) + 2:
            return False

        # Must start and end with same tools
        if candidate[0] != base[0] or candidate[-1] != base[-1]:
            return False

        # Check that base is a subsequence of candidate
        base_idx = 0
        for tool in candidate:
            if base_idx < len(base) and tool == base[base_idx]:
                base_idx += 1

        return base_idx == len(base)
