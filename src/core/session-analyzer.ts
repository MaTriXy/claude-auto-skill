/**
 * Session Analyzer - Analyzes full coding agent session history.
 *
 * Goes beyond tool patterns to understand:
 * - Full conversation context (user intents, reasoning)
 * - Decision-making patterns (how problems were approached)
 * - Problem-solving strategies (debugging, refactoring, TDD)
 * - Learning patterns (what worked, what didn't)
 *
 * Ported from Python core/session_analyzer.py
 */

import type {
  ConversationTurn,
  SessionContext,
  ProblemSolvingPattern,
  ToolEvent,
} from "../types";

/** Keywords for categorizing user intents. */
const INTENT_KEYWORDS: Record<string, string[]> = {
  debug: ["bug", "error", "fix", "issue", "problem", "not working", "broken"],
  implement: ["create", "add", "implement", "build", "make", "new feature"],
  refactor: ["refactor", "clean up", "reorganize", "improve", "optimize"],
  test: ["test", "TDD", "unit test", "testing", "coverage"],
  explore: ["understand", "explain", "how does", "what is", "show me"],
  document: ["document", "comment", "README", "docs", "documentation"],
};

/** Workflow patterns based on tool sequences and context keywords. */
const WORKFLOW_PATTERNS: Record<
  string,
  { toolSequence: string[]; keywords: string[] }
> = {
  TDD: {
    toolSequence: ["Write", "Bash", "Edit", "Bash"],
    keywords: ["test", "TDD", "red-green-refactor"],
  },
  "Debug-Systematic": {
    toolSequence: ["Read", "Grep", "Bash", "Edit"],
    keywords: ["error", "bug", "debug", "fix"],
  },
  "Refactor-Safe": {
    toolSequence: ["Read", "Edit", "Bash"],
    keywords: ["refactor", "improve", "clean"],
  },
  "Explore-Then-Implement": {
    toolSequence: ["Grep", "Read", "Write"],
    keywords: ["understand", "then", "create"],
  },
};

/**
 * Check if `subsequence` appears as a contiguous slice in `sequence`.
 */
function containsSubsequence(sequence: string[], subsequence: string[]): boolean {
  const subLen = subsequence.length;
  for (let i = 0; i <= sequence.length - subLen; i++) {
    let matches = true;
    for (let j = 0; j < subLen; j++) {
      if (sequence[i + j] !== subsequence[j]) {
        matches = false;
        break;
      }
    }
    if (matches) return true;
  }
  return false;
}

/**
 * Parse ISO-8601 timestamp string to milliseconds since epoch.
 * Returns 0 if parsing fails.
 */
function parseTimestamp(ts: string): number {
  const ms = Date.parse(ts);
  return isNaN(ms) ? 0 : ms;
}

/**
 * Get the count of each string in an array and return the one with the highest count.
 */
function mostCommon(items: string[]): string | null {
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
 * Create a session analyzer for extracting rich context from tool event sessions.
 *
 * @returns Object with session analysis methods
 */
export function createSessionAnalyzer(): {
  analyzeSession(
    sessionId: string,
    events: ToolEvent[],
    conversationLog?: string
  ): SessionContext;
  detectProblemSolvingPatterns(
    sessions: Array<{ sessionId: string; events: ToolEvent[] }>
  ): ProblemSolvingPattern[];
} {
  /**
   * Parse conversation turns from tool events.
   * Groups consecutive events by 60-second gaps.
   */
  function parseConversationTurns(
    sessionId: string,
    events: ToolEvent[],
    _conversationLog?: string
  ): ConversationTurn[] {
    const turns: ConversationTurn[] = [];
    let currentTurnTools: string[] = [];
    let currentTimestamp: string | null = null;

    for (const event of events) {
      if (currentTimestamp !== null) {
        const gap =
          parseTimestamp(event.timestamp) - parseTimestamp(currentTimestamp);
        if (gap > 60_000) {
          // Gap > 1 minute means new turn
          if (currentTurnTools.length > 0) {
            turns.push({
              sessionId,
              timestamp: currentTimestamp,
              userMessage: null,
              claudeResponse: null,
              toolsUsed: currentTurnTools,
              intentCategory: null,
              problemDomain: null,
              outcome: null,
            });
          }
          currentTurnTools = [];
        }
      }

      currentTurnTools.push(event.toolName);
      currentTimestamp = event.timestamp;
    }

    // Don't forget the last turn
    if (currentTurnTools.length > 0 && currentTimestamp !== null) {
      turns.push({
        sessionId,
        timestamp: currentTimestamp,
        userMessage: null,
        claudeResponse: null,
        toolsUsed: currentTurnTools,
        intentCategory: null,
        problemDomain: null,
        outcome: null,
      });
    }

    return turns;
  }

  /**
   * Detect the primary user intent for the session based on keyword scoring.
   */
  function detectPrimaryIntent(
    turns: ConversationTurn[]
  ): string | null {
    if (turns.length === 0) return null;

    const intentScores: Record<string, number> = {};
    for (const intent of Object.keys(INTENT_KEYWORDS)) {
      intentScores[intent] = 0;
    }

    for (const turn of turns) {
      if (turn.userMessage) {
        const messageLower = turn.userMessage.toLowerCase();
        for (const [intent, keywords] of Object.entries(INTENT_KEYWORDS)) {
          for (const keyword of keywords) {
            if (messageLower.includes(keyword)) {
              intentScores[intent]++;
            }
          }
        }
      }
    }

    const maxScore = Math.max(...Object.values(intentScores));
    if (maxScore > 0) {
      for (const [intent, score] of Object.entries(intentScores)) {
        if (score === maxScore) return intent;
      }
    }

    return null;
  }

  /**
   * Extract problem domains from file paths in tool inputs.
   */
  function extractProblemDomains(
    _turns: ConversationTurn[],
    events: ToolEvent[]
  ): string[] {
    const domains = new Set<string>();

    for (const event of events) {
      const pathValue =
        (event.toolInput?.path as string) ??
        (event.toolInput?.file_path as string) ??
        null;

      if (pathValue) {
        // Extract parent directory as domain
        const parts = pathValue.replace(/\\/g, "/").split("/").filter(Boolean);
        if (parts.length > 1) {
          domains.add(parts[parts.length - 2]);
        }
      }
    }

    return [...domains].sort().slice(0, 5);
  }

  /**
   * Detect the workflow type by matching tool sequences against known patterns.
   */
  function detectWorkflowType(
    events: ToolEvent[],
    _turns: ConversationTurn[]
  ): string | null {
    const toolSequence = events.map((e) => e.toolName);

    for (const [workflowType, patternInfo] of Object.entries(WORKFLOW_PATTERNS)) {
      if (containsSubsequence(toolSequence, patternInfo.toolSequence)) {
        return workflowType;
      }
    }

    return null;
  }

  /**
   * Calculate indicators of session success.
   */
  function calculateSuccessIndicators(
    events: ToolEvent[]
  ): Record<string, unknown> {
    const totalTools = events.length;
    const successfulTools = events.filter((e) => e.success).length;

    let durationMinutes = 0;
    if (events.length >= 2) {
      const startMs = parseTimestamp(events[0].timestamp);
      const endMs = parseTimestamp(events[events.length - 1].timestamp);
      durationMinutes = (endMs - startMs) / 60_000;
    }

    return {
      tool_success_rate: totalTools > 0 ? successfulTools / totalTools : 0,
      total_tools_used: totalTools,
      session_duration_minutes: durationMinutes,
    };
  }

  /**
   * Create an empty session context when no events are available.
   */
  function createEmptyContext(sessionId: string): SessionContext {
    const now = new Date().toISOString();
    return {
      sessionId,
      startTime: now,
      endTime: now,
      projectPath: "",
      turns: [],
      primaryIntent: null,
      problemDomains: [],
      workflowType: null,
      successIndicators: {},
      keyDecisions: [],
    };
  }

  /**
   * Analyze a complete session with full context.
   *
   * @param sessionId - Session identifier
   * @param events - Tool events for this session
   * @param conversationLog - Optional full conversation transcript
   * @returns SessionContext with rich analysis
   */
  function analyzeSession(
    sessionId: string,
    events: ToolEvent[],
    conversationLog?: string
  ): SessionContext {
    if (events.length === 0) {
      return createEmptyContext(sessionId);
    }

    const turns = parseConversationTurns(sessionId, events, conversationLog);
    const primaryIntent = detectPrimaryIntent(turns);
    const problemDomains = extractProblemDomains(turns, events);
    const workflowType = detectWorkflowType(events, turns);
    const successIndicators = calculateSuccessIndicators(events);

    return {
      sessionId,
      startTime: events[0].timestamp,
      endTime: events[events.length - 1].timestamp,
      projectPath: events[0].projectPath,
      turns,
      primaryIntent,
      problemDomains,
      workflowType,
      successIndicators,
      keyDecisions: [],
    };
  }

  /**
   * Detect high-level problem-solving patterns across sessions.
   *
   * Groups sessions by workflow type, then creates ProblemSolvingPattern
   * objects for groups meeting the minimum occurrence threshold.
   *
   * @param sessions - Array of session data with events
   * @returns List of detected problem-solving patterns sorted by success rate
   */
  function detectProblemSolvingPatterns(
    sessions: Array<{ sessionId: string; events: ToolEvent[] }>
  ): ProblemSolvingPattern[] {
    // Analyze each session
    const sessionContexts = sessions.map((s) =>
      analyzeSession(s.sessionId, s.events)
    );

    // Group by workflow type
    const workflowGroups = new Map<string, SessionContext[]>();
    for (const ctx of sessionContexts) {
      if (ctx.workflowType) {
        const existing = workflowGroups.get(ctx.workflowType);
        if (existing) {
          existing.push(ctx);
        } else {
          workflowGroups.set(ctx.workflowType, [ctx]);
        }
      }
    }

    // Create patterns from groups (minimum 2 occurrences)
    const patterns: ProblemSolvingPattern[] = [];
    for (const [workflowType, contexts] of workflowGroups) {
      if (contexts.length < 2) continue;

      // Calculate success rate
      const successCount = contexts.filter(
        (ctx) =>
          (ctx.successIndicators as Record<string, number>).tool_success_rate >
          0.8
      ).length;
      const successRate = successCount / contexts.length;

      // Get common domains
      const allDomains: string[] = [];
      for (const ctx of contexts) {
        allDomains.push(...ctx.problemDomains);
      }
      const domainCounts = new Map<string, number>();
      for (const d of allDomains) {
        domainCounts.set(d, (domainCounts.get(d) ?? 0) + 1);
      }
      const topDomains = [...domainCounts.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(([d]) => d);

      // Get primary intents
      const primaryIntents = [
        ...new Set(
          contexts
            .map((ctx) => ctx.primaryIntent)
            .filter((i): i is string => i !== null && i !== undefined)
        ),
      ];

      patterns.push({
        patternId: `ps-${workflowType}`,
        patternType: workflowType,
        description: `Problem-solving pattern: ${workflowType}`,
        workflowSteps: [
          "Analyze problem",
          "Plan approach",
          "Implement solution",
          "Verify",
        ],
        successRate,
        occurrenceCount: contexts.length,
        exampleSessions: contexts.slice(0, 3).map((ctx) => ctx.sessionId),
        contextualIndicators: {
          primary_intents: primaryIntents,
          common_domains: topDomains,
        },
      });
    }

    // Sort by success rate descending
    patterns.sort((a, b) => b.successRate - a.successRate);
    return patterns;
  }

  return {
    analyzeSession,
    detectProblemSolvingPatterns,
  };
}
