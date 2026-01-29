/**
 * Pattern Detector - Enhanced v2 orchestrator for workflow pattern detection.
 *
 * V1 Functionality (preserved):
 * - Detects tool usage patterns from event sessions
 * - Calculates confidence scores with weighted formula
 * - Generates pattern IDs via SHA-256
 *
 * V2 Enhancements:
 * - Integrates session context analysis
 * - Detects design patterns (architectural, coding, workflow)
 * - Provides richer metadata for skill generation
 *
 * Ported from Python core/pattern_detector.py
 */

import crypto from "node:crypto";

import type {
  DetectedPattern,
  ToolEvent,
  SequenceMatch,
} from "../types";
import { createSequenceMatcher } from "./sequence-matcher";
import { createSessionAnalyzer } from "./session-analyzer";
import { createDesignPatternDetector } from "./design-pattern-detector";

// ---------------------------------------------------------------------------
// Tool verb map (tool name -> human-readable verb for naming)
// ---------------------------------------------------------------------------

const TOOL_VERBS: Record<string, string> = {
  Read: "read",
  Write: "write",
  Edit: "edit",
  Bash: "run",
  Grep: "search",
  Glob: "find",
  WebFetch: "fetch",
  WebSearch: "search",
  Task: "delegate",
};

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

/** Options for the pattern detection pipeline. */
export interface PatternDetectorOptions {
  /** Minimum times a sequence must appear. Default: 3 */
  minOccurrences?: number;
  /** Minimum tool sequence length. Default: 2 */
  minSequenceLength?: number;
  /** Maximum tool sequence length. Default: 10 */
  maxSequenceLength?: number;
  /** Analysis window in days. Default: 7 */
  lookbackDays?: number;
  /** Enable v2 enhancements (session/design pattern analysis). Default: true */
  enableV2?: boolean;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Parse an ISO-8601 timestamp to milliseconds since epoch.
 * Returns 0 if the string cannot be parsed.
 */
function parseTs(ts: string): number {
  const ms = Date.parse(ts);
  return isNaN(ms) ? 0 : ms;
}

/**
 * Generate a SHA-256 based pattern ID (first 12 hex chars).
 */
function generatePatternId(sequence: string[]): string {
  const seqStr = sequence.join("-");
  return crypto.createHash("sha256").update(seqStr).digest("hex").slice(0, 12);
}

/**
 * Generate a human-readable name from a tool sequence.
 */
function generateName(tools: string[]): string {
  if (tools.length === 0) return "unknown-workflow";

  const firstVerb = TOOL_VERBS[tools[0]] ?? tools[0].toLowerCase();
  const lastVerb = TOOL_VERBS[tools[tools.length - 1]] ?? tools[tools.length - 1].toLowerCase();

  if (tools.length === 2) {
    return `${firstVerb}-then-${lastVerb}`;
  }
  return `${firstVerb}-and-${lastVerb}`;
}

/**
 * Generate a description from a tool sequence.
 */
function generateDescription(tools: string[]): string {
  if (tools.length === 0) return "Unknown workflow pattern";
  return `Workflow pattern: ${tools.join(", ")}`;
}

/**
 * Find events in a session matching a tool sequence (contiguous).
 */
function findSequenceInSession(
  sequence: string[],
  events: ToolEvent[]
): ToolEvent[] {
  const toolNames = events.map((e) => e.toolName);
  for (let start = 0; start <= toolNames.length - sequence.length; start++) {
    let match = true;
    for (let j = 0; j < sequence.length; j++) {
      if (toolNames[start + j] !== sequence[j]) {
        match = false;
        break;
      }
    }
    if (match) {
      return events.slice(start, start + sequence.length);
    }
  }
  return [];
}

/**
 * Calculate confidence score for a pattern using a weighted formula.
 *
 * Weights: occurrence(0.4), length(0.2), success(0.25), recency(0.15)
 */
function calculateConfidence(
  occurrenceCount: number,
  sequenceLength: number,
  successRate: number,
  lastSeenMs: number
): number {
  // Occurrence score: logarithmic scaling
  const occurrenceScore = Math.min(
    1.0,
    Math.log(occurrenceCount + 1) / Math.log(10)
  );

  // Length score: optimal range is 3-5
  let lengthScore: number;
  if (sequenceLength >= 3 && sequenceLength <= 5) {
    lengthScore = 1.0;
  } else if (sequenceLength === 2) {
    lengthScore = 0.7;
  } else if (sequenceLength > 5) {
    lengthScore = Math.max(0.5, 1.0 - (sequenceLength - 5) * 0.1);
  } else {
    lengthScore = 0.5;
  }

  // Success score: direct
  const successScore = successRate;

  // Recency score: decay per day since last seen
  const nowMs = Date.now();
  const daysSinceLast = (nowMs - lastSeenMs) / 86_400_000;
  const recencyScore = Math.max(0.5, 1.0 - daysSinceLast * 0.05);

  const confidence =
    occurrenceScore * 0.4 +
    lengthScore * 0.2 +
    successScore * 0.25 +
    recencyScore * 0.15;

  return Math.min(1.0, Math.max(0.0, confidence));
}

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

/**
 * Create a pattern detector that orchestrates sequence matching,
 * session analysis, and design pattern detection.
 *
 * @returns Object with pattern detection methods
 */
export function createPatternDetector(): {
  detectPatterns(
    eventSessions: ToolEvent[][],
    options?: PatternDetectorOptions
  ): DetectedPattern[];
  getPendingPatterns(
    eventSessions: ToolEvent[][],
    minConfidence?: number
  ): DetectedPattern[];
} {
  const sessionAnalyzer = createSessionAnalyzer();
  const designPatternDetector = createDesignPatternDetector();

  /**
   * Build a DetectedPattern from a SequenceMatch plus event session data.
   */
  function createPattern(
    match: SequenceMatch,
    eventSessions: ToolEvent[][],
    enableV2: boolean
  ): DetectedPattern | null {
    if (match.sessionIndices.length === 0) return null;

    // Collect basic metadata across sessions
    const sessionIds: string[] = [];
    let firstSeenMs: number | null = null;
    let lastSeenMs: number | null = null;
    let successCount = 0;
    let totalCount = 0;

    for (const sessionIdx of match.sessionIndices) {
      if (sessionIdx >= eventSessions.length) continue;

      const events = eventSessions[sessionIdx];
      if (events.length === 0) continue;

      sessionIds.push(events[0].sessionId);

      const seqEvents = findSequenceInSession(match.sequence, events);
      if (seqEvents.length > 0) {
        totalCount++;
        if (seqEvents.every((e) => e.success)) {
          successCount++;
        }

        const seqStartMs = parseTs(seqEvents[0].timestamp);
        const seqEndMs = parseTs(seqEvents[seqEvents.length - 1].timestamp);

        if (firstSeenMs === null || seqStartMs < firstSeenMs) {
          firstSeenMs = seqStartMs;
        }
        if (lastSeenMs === null || seqEndMs > lastSeenMs) {
          lastSeenMs = seqEndMs;
        }
      }
    }

    const now = Date.now();
    if (firstSeenMs === null) firstSeenMs = now;
    if (lastSeenMs === null) lastSeenMs = now;

    const successRate = totalCount > 0 ? successCount / totalCount : 1.0;

    const confidence = calculateConfidence(
      match.occurrences,
      match.sequence.length,
      successRate,
      lastSeenMs
    );

    const suggestedName = generateName(match.sequence);
    const suggestedDescription = generateDescription(match.sequence);
    const uniqueSessionIds = [...new Set(sessionIds)];

    const pattern: DetectedPattern = {
      id: generatePatternId(match.sequence),
      toolSequence: match.sequence,
      occurrenceCount: match.occurrences,
      confidence,
      sessionIds: uniqueSessionIds,
      firstSeen: new Date(firstSeenMs).toISOString(),
      lastSeen: new Date(lastSeenMs).toISOString(),
      successRate,
      suggestedName,
      suggestedDescription,
      sessionContext: null,
      codeContext: null,
      designPatterns: [],
      problemSolvingApproach: null,
      mentalContext: null,
    };

    // V2 enhancements
    if (enableV2) {
      enhanceWithV2(pattern, eventSessions, match.sessionIndices);
    }

    return pattern;
  }

  /**
   * Enhance a pattern with v2 session context and design pattern data.
   */
  function enhanceWithV2(
    pattern: DetectedPattern,
    eventSessions: ToolEvent[][],
    sessionIndices: number[]
  ): void {
    // Session context analysis: analyze up to 5 sessions
    const contextsToAnalyze = sessionIndices.slice(0, 5);
    const sessionContexts = contextsToAnalyze
      .filter((idx) => idx < eventSessions.length && eventSessions[idx].length > 0)
      .map((idx) => {
        const events = eventSessions[idx];
        return sessionAnalyzer.analyzeSession(events[0].sessionId, events);
      });

    if (sessionContexts.length > 0) {
      // Aggregate session insights
      const primaryIntents = sessionContexts
        .map((ctx) => ctx.primaryIntent)
        .filter((i): i is string => i !== null && i !== undefined);

      const allDomains: string[] = [];
      for (const ctx of sessionContexts) {
        allDomains.push(...ctx.problemDomains);
      }

      const workflowTypes = sessionContexts
        .map((ctx) => ctx.workflowType)
        .filter((w): w is string => w !== null && w !== undefined);

      const avgToolSuccess =
        sessionContexts.reduce(
          (sum, ctx) =>
            sum +
            ((ctx.successIndicators as Record<string, number>)
              .tool_success_rate ?? 0),
          0
        ) / sessionContexts.length;

      const avgDuration =
        sessionContexts.reduce(
          (sum, ctx) =>
            sum +
            ((ctx.successIndicators as Record<string, number>)
              .session_duration_minutes ?? 0),
          0
        ) / sessionContexts.length;

      pattern.sessionContext = {
        primaryIntent: getMostFrequent(primaryIntents),
        problemDomains: [...new Set(allDomains)].slice(0, 5),
        workflowType: getMostFrequent(workflowTypes),
        toolSuccessRate: Math.round(avgToolSuccess * 100) / 100,
        avgSessionDurationMinutes:
          Math.round(avgDuration * 10) / 10,
      };

      // Problem-solving approach
      const workflowType = pattern.sessionContext.workflowType as string | null;
      if (workflowType) {
        pattern.problemSolvingApproach =
          createProblemSolvingApproach(workflowType);
      }
    }

    // Design pattern detection from tool sequence
    const workflowPattern = designPatternDetector.detectWorkflowPattern(
      pattern.toolSequence,
      pattern.sessionContext ?? undefined
    );
    if (workflowPattern) {
      pattern.designPatterns = [
        {
          name: workflowPattern.patternName,
          type: workflowPattern.patternType,
          confidence:
            Math.round(workflowPattern.confidence * 100) / 100,
          description: workflowPattern.description,
          indicators: workflowPattern.indicators.slice(0, 5),
        },
      ];
    }
  }

  /**
   * Get the most frequently occurring string in an array.
   */
  function getMostFrequent(items: string[]): string | null {
    if (items.length === 0) return null;
    const counts = new Map<string, number>();
    for (const item of items) {
      counts.set(item, (counts.get(item) ?? 0) + 1);
    }
    let best: string | null = null;
    let bestCount = 0;
    for (const [item, count] of counts) {
      if (count > bestCount) {
        best = item;
        bestCount = count;
      }
    }
    return best;
  }

  /**
   * Create a problem-solving approach metadata object for a given workflow type.
   */
  function createProblemSolvingApproach(
    workflowType: string
  ): Record<string, unknown> {
    const approaches: Record<string, Record<string, unknown>> = {
      TDD: {
        type: "TDD",
        description: "Test-Driven Development workflow",
        whenToUse:
          "When building new features or fixing bugs with test coverage",
        steps: [
          "Write a failing test that defines desired behavior",
          "Run tests to confirm the failure (Red)",
          "Write minimal code to make the test pass (Green)",
          "Run tests to confirm they pass",
          "Refactor code while keeping tests green",
        ],
        benefits: [
          "Better test coverage",
          "Forces thinking about requirements first",
          "Confidence when refactoring",
        ],
        tradeOffs: [
          "Slower initial development",
          "Requires discipline to follow the cycle",
        ],
      },
      "Refactor-Safe": {
        type: "Refactor-Safe",
        description: "Safe refactoring with continuous testing",
        whenToUse:
          "When improving code structure without changing behavior",
        steps: [
          "Read and understand the current implementation",
          "Identify code smells and refactoring opportunities",
          "Make small, incremental changes",
          "Run tests after each change to ensure behavior preservation",
          "Commit working state before next refactor",
        ],
        benefits: [
          "Maintains test coverage throughout",
          "Reduces risk of introducing bugs",
          "Clear rollback points",
        ],
        tradeOffs: [
          "Slower than rewriting from scratch",
          "Requires good test coverage to be safe",
        ],
      },
      "Debug-Systematic": {
        type: "Debug-Systematic",
        description: "Systematic debugging approach",
        whenToUse:
          "When tracking down bugs or unexpected behavior",
        steps: [
          "Read code to understand the flow",
          "Search for error messages or suspicious patterns",
          "Add logging or debugging statements",
          "Run code to observe behavior",
          "Form hypothesis and test it",
          "Fix the issue and verify",
        ],
        benefits: [
          "Structured approach reduces frustration",
          "Learns about codebase during debugging",
          "Verifiable fix",
        ],
        tradeOffs: ["Can be time-consuming for complex issues"],
      },
    };

    return (
      approaches[workflowType] ?? {
        type: workflowType,
        description: `Detected workflow pattern: ${workflowType}`,
      }
    );
  }

  /**
   * Detect workflow patterns from grouped event sessions.
   *
   * Pipeline:
   * 1. Extract tool name sequences from each session
   * 2. Run sequence matcher to find repeated subsequences
   * 3. For each match, collect session IDs, timestamps, success rates
   * 4. Calculate confidence with weighted formula
   * 5. Generate name, description, and pattern ID
   * 6. Optionally enhance with session context and design patterns (v2)
   *
   * @param eventSessions - Array of session event arrays
   * @param options - Detection configuration
   * @returns Array of DetectedPattern sorted by confidence desc
   */
  function detectPatterns(
    eventSessions: ToolEvent[][],
    options?: PatternDetectorOptions
  ): DetectedPattern[] {
    if (eventSessions.length === 0) return [];

    const minOccurrences = options?.minOccurrences ?? 3;
    const minSequenceLength = options?.minSequenceLength ?? 2;
    const maxSequenceLength = options?.maxSequenceLength ?? 10;
    const enableV2 = options?.enableV2 ?? true;

    // Extract tool name sequences from each session
    const sequences: string[][] = eventSessions
      .filter((events) => events.length >= minSequenceLength)
      .map((events) => events.map((e) => e.toolName));

    if (sequences.length === 0) return [];

    // Find common subsequences
    const matcher = createSequenceMatcher({
      minLength: minSequenceLength,
      maxLength: maxSequenceLength,
      minOccurrences,
    });

    const matches = matcher.findCommonSubsequences(sequences);
    if (matches.length === 0) return [];

    // Convert matches to DetectedPatterns
    const patterns: DetectedPattern[] = [];
    for (const match of matches) {
      const pattern = createPattern(match, eventSessions, enableV2);
      if (pattern) {
        patterns.push(pattern);
      }
    }

    // Sort by confidence descending
    patterns.sort((a, b) => b.confidence - a.confidence);
    return patterns;
  }

  /**
   * Get patterns that meet a minimum confidence threshold.
   *
   * Convenience wrapper around detectPatterns with a confidence filter.
   *
   * @param eventSessions - Array of session event arrays
   * @param minConfidence - Minimum confidence score. Default: 0.7
   * @returns Filtered array of DetectedPattern
   */
  function getPendingPatterns(
    eventSessions: ToolEvent[][],
    minConfidence: number = 0.7
  ): DetectedPattern[] {
    const patterns = detectPatterns(eventSessions);
    return patterns.filter((p) => p.confidence >= minConfidence);
  }

  return {
    detectPatterns,
    getPendingPatterns,
  };
}
