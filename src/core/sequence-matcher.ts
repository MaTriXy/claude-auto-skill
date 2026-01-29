/**
 * Sequence Matcher - Finds repeated subsequences in tool sequences.
 *
 * Uses a sliding window approach to identify common patterns across
 * multiple sessions. Prioritizes longer sequences and higher occurrence counts.
 *
 * Ported from Python core/sequence_matcher.py
 */

import type { SequenceMatch } from "../types";

/** Options for configuring the sequence matcher. */
export interface SequenceMatcherOptions {
  /** Minimum subsequence length to detect. Default: 2 */
  minLength?: number;
  /** Maximum subsequence length to detect. Default: 10 */
  maxLength?: number;
  /** Minimum times a sequence must appear across sessions. Default: 3 */
  minOccurrences?: number;
}

/**
 * Create a sequence matcher that finds repeated subsequences across
 * multiple tool sequences.
 *
 * @param options - Configuration options for the matcher
 * @returns Object with sequence matching methods
 */
export function createSequenceMatcher(options?: SequenceMatcherOptions): {
  findCommonSubsequences(sequences: string[][]): SequenceMatch[];
  findPatternVariations(
    baseSequence: string[],
    sequences: string[][],
    maxVariations?: number
  ): string[][];
} {
  const minLength = options?.minLength ?? 2;
  const maxLength = options?.maxLength ?? 10;
  const minOccurrences = options?.minOccurrences ?? 3;

  /**
   * Check if `shorter` is a contiguous subsequence of `longer`
   * using the join("|||") approach.
   */
  function isSubsequenceOf(shorter: string[], longer: string[]): boolean {
    if (shorter.length >= longer.length) {
      return false;
    }
    const shorterStr = shorter.join("|||");
    const longerStr = longer.join("|||");
    return longerStr.includes(shorterStr);
  }

  /**
   * Remove shorter sequences that are fully contained in longer ones
   * with the same (or subset of) session indices.
   */
  function removeSubsumedMatches(matches: SequenceMatch[]): SequenceMatch[] {
    if (matches.length === 0) {
      return [];
    }

    // Sort by length descending to process longer sequences first
    const sorted = [...matches].sort(
      (a, b) => b.sequence.length - a.sequence.length
    );
    const kept: SequenceMatch[] = [];

    for (const match of sorted) {
      let isSubsumed = false;

      for (const longer of kept) {
        if (isSubsequenceOf(match.sequence, longer.sequence)) {
          // Check if all occurrences are explained by the longer sequence
          const matchSessionSet = new Set(match.sessionIndices);
          const longerSessionSet = new Set(longer.sessionIndices);
          const allCovered = [...matchSessionSet].every((idx) =>
            longerSessionSet.has(idx)
          );

          if (allCovered) {
            isSubsumed = true;
            break;
          }
        }
      }

      if (!isSubsumed) {
        kept.push(match);
      }
    }

    return kept;
  }

  /**
   * Find common subsequences across multiple tool sequences.
   *
   * @param sequences - List of tool name sequences (one per session)
   * @returns List of SequenceMatch objects, sorted by (length desc, occurrences desc)
   */
  function findCommonSubsequences(sequences: string[][]): SequenceMatch[] {
    if (sequences.length === 0) {
      return [];
    }

    // Extract all subsequences of valid lengths
    const subsequenceLocations = new Map<string, number[]>();

    for (let sessionIdx = 0; sessionIdx < sequences.length; sessionIdx++) {
      const sequence = sequences[sessionIdx];
      const seenInSession = new Set<string>();

      const upperLen = Math.min(maxLength + 1, sequence.length + 1);
      for (let length = minLength; length < upperLen; length++) {
        for (let start = 0; start <= sequence.length - length; start++) {
          const subseq = sequence.slice(start, start + length);
          const key = subseq.join("|||");

          // Only count once per session
          if (!seenInSession.has(key)) {
            seenInSession.add(key);
            const existing = subsequenceLocations.get(key);
            if (existing) {
              existing.push(sessionIdx);
            } else {
              subsequenceLocations.set(key, [sessionIdx]);
            }
          }
        }
      }
    }

    // Filter to sequences meeting minimum occurrence threshold
    const matches: SequenceMatch[] = [];
    for (const [key, sessionIndices] of subsequenceLocations) {
      if (sessionIndices.length >= minOccurrences) {
        matches.push({
          sequence: key.split("|||"),
          occurrences: sessionIndices.length,
          sessionIndices,
        });
      }
    }

    // Remove subsequences that are fully contained in longer matches
    const filtered = removeSubsumedMatches(matches);

    // Sort by length (desc) then occurrences (desc)
    filtered.sort((a, b) => {
      const lenDiff = b.sequence.length - a.sequence.length;
      if (lenDiff !== 0) return lenDiff;
      return b.occurrences - a.occurrences;
    });

    return filtered;
  }

  /**
   * Check if `candidate` is a variation of `base`.
   * A variation has the same start and end but may have 1-2 extra steps.
   */
  function isVariationOf(base: string[], candidate: string[]): boolean {
    if (
      candidate.length <= base.length ||
      candidate.length > base.length + 2
    ) {
      return false;
    }

    // Must start and end with same tools
    if (candidate[0] !== base[0] || candidate[candidate.length - 1] !== base[base.length - 1]) {
      return false;
    }

    // Check that base is a subsequence of candidate
    let baseIdx = 0;
    for (const tool of candidate) {
      if (baseIdx < base.length && tool === base[baseIdx]) {
        baseIdx++;
      }
    }

    return baseIdx === base.length;
  }

  /**
   * Find variations of a base sequence (e.g., with optional steps).
   *
   * This helps identify patterns that are similar but not identical,
   * which could be combined into a single skill with optional steps.
   *
   * @param baseSequence - The base sequence to find variations of
   * @param sequences - All available sequences to search through
   * @param maxVariations - Maximum number of variations to return. Default: 3
   * @returns List of variation sequences
   */
  function findPatternVariations(
    baseSequence: string[],
    sequences: string[][],
    maxVariations: number = 3
  ): string[][] {
    const variations: string[][] = [];

    for (const sequence of sequences) {
      if (sequence.length < baseSequence.length) {
        continue;
      }

      for (
        let start = 0;
        start <= sequence.length - baseSequence.length;
        start++
      ) {
        // Check a window that is slightly larger than base
        const candidate = sequence.slice(start, start + baseSequence.length + 2);
        if (isVariationOf(baseSequence, candidate)) {
          // Check for duplicates using join comparison
          const candidateKey = candidate.join("|||");
          const isDuplicate = variations.some(
            (v) => v.join("|||") === candidateKey
          );
          if (!isDuplicate) {
            variations.push(candidate);
            if (variations.length >= maxVariations) {
              return variations;
            }
          }
        }
      }
    }

    return variations;
  }

  return {
    findCommonSubsequences,
    findPatternVariations,
  };
}
