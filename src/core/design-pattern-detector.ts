/**
 * Design Pattern Detector - Identifies architectural, coding, and workflow patterns.
 *
 * Detects patterns at multiple levels:
 * - Architectural patterns (MVC, Repository, Factory, Singleton, etc.)
 * - Coding patterns (error handling, API design, async, decorators)
 * - Workflow patterns (TDD, refactoring approaches, debugging strategies)
 *
 * Ported from Python core/design_pattern_detector.py
 */

import type { DesignPattern, PatternContext } from "../types";

/** Definition of a recognizable pattern with its detection indicators. */
interface PatternDefinition {
  indicators: string[];
  description: string;
  minConfidence: number;
}

/** Definition of a workflow pattern with tool sequence. */
interface WorkflowPatternDefinition {
  toolSequence: string[];
  description: string;
  indicators: string[];
}

// ---------------------------------------------------------------------------
// Pattern catalogs
// ---------------------------------------------------------------------------

const ARCHITECTURAL_PATTERNS: Record<string, PatternDefinition> = {
  MVC: {
    indicators: [
      "model",
      "view",
      "controller",
      "models/",
      "views/",
      "controllers/",
    ],
    description: "Model-View-Controller separation pattern",
    minConfidence: 0.6,
  },
  Repository: {
    indicators: ["repository", "repo", "data_access", "dal"],
    description: "Repository pattern for data access abstraction",
    minConfidence: 0.5,
  },
  Factory: {
    indicators: ["factory", "create_", "builder"],
    description: "Factory pattern for object creation",
    minConfidence: 0.5,
  },
  Singleton: {
    indicators: ["singleton", "_instance", "get_instance"],
    description: "Singleton pattern for single-instance classes",
    minConfidence: 0.6,
  },
  Strategy: {
    indicators: ["strategy", "algorithm", "policy"],
    description: "Strategy pattern for interchangeable algorithms",
    minConfidence: 0.5,
  },
  Observer: {
    indicators: ["observer", "subscriber", "listener", "event"],
    description: "Observer pattern for event handling",
    minConfidence: 0.5,
  },
  Adapter: {
    indicators: ["adapter", "wrapper", "facade"],
    description: "Adapter pattern for interface compatibility",
    minConfidence: 0.5,
  },
  "Dependency-Injection": {
    indicators: ["inject", "container", "provider", "di_"],
    description: "Dependency Injection pattern",
    minConfidence: 0.6,
  },
};

const CODING_PATTERNS: Record<string, PatternDefinition> = {
  "Error-First-Handling": {
    indicators: ["try", "except", "raise", "error", "exception"],
    description: "Error-first error handling pattern",
    minConfidence: 0.4,
  },
  "REST-API-Design": {
    indicators: ["@app.route", "@router", "GET", "POST", "PUT", "DELETE"],
    description: "RESTful API design pattern",
    minConfidence: 0.5,
  },
  "Async-Pattern": {
    indicators: ["async", "await", "asyncio", "concurrent"],
    description: "Asynchronous programming pattern",
    minConfidence: 0.5,
  },
  "Decorator-Pattern": {
    indicators: ["@decorator", "@property", "@staticmethod"],
    description: "Python decorator pattern",
    minConfidence: 0.4,
  },
  "Context-Manager": {
    indicators: ["__enter__", "__exit__", "with ", "contextmanager"],
    description: "Context manager pattern (with statement)",
    minConfidence: 0.5,
  },
  "Builder-Pattern": {
    indicators: ["builder", "build()", "with_", "set_"],
    description: "Fluent builder pattern",
    minConfidence: 0.5,
  },
};

const WORKFLOW_PATTERNS: Record<string, WorkflowPatternDefinition> = {
  TDD: {
    toolSequence: ["Write", "Bash", "Edit", "Bash"],
    description: "Test-Driven Development workflow",
    indicators: ["test", "assert", "pytest", "unittest"],
  },
  "Refactor-Safe": {
    toolSequence: ["Read", "Edit", "Bash"],
    description: "Safe refactoring with tests",
    indicators: ["refactor", "test", "extract", "rename"],
  },
  "Debug-Systematic": {
    toolSequence: ["Read", "Grep", "Bash", "Edit"],
    description: "Systematic debugging approach",
    indicators: ["debug", "print", "log", "trace"],
  },
  "Explore-Then-Implement": {
    toolSequence: ["Grep", "Read", "Read", "Write"],
    description: "Exploration before implementation",
    indicators: ["understand", "explore", "analyze"],
  },
};

// ---------------------------------------------------------------------------
// Predefined pattern contexts
// ---------------------------------------------------------------------------

const PATTERN_CONTEXTS: Record<string, PatternContext> = {
  MVC: {
    patternName: "MVC",
    whenToUse:
      "Building web applications with clear separation of concerns",
    benefits: [
      "Separates business logic from presentation",
      "Easier to test and maintain",
      "Multiple views can share same model",
    ],
    tradeOffs: [
      "Can be overkill for simple applications",
      "More files and indirection",
    ],
    commonMistakes: [
      "Putting business logic in controllers",
      "Tight coupling between layers",
    ],
  },
  Repository: {
    patternName: "Repository",
    whenToUse: "When you need to abstract data access layer",
    benefits: [
      "Decouples business logic from data access",
      "Easy to swap data sources",
      "Centralized data access logic",
    ],
    tradeOffs: [
      "Additional abstraction layer",
      "Can be over-engineering",
    ],
    commonMistakes: [
      "Leaking data access concerns to business layer",
    ],
  },
  TDD: {
    patternName: "TDD",
    whenToUse: "When building new features or fixing bugs",
    benefits: [
      "Better test coverage",
      "Forces you to think about requirements",
      "Refactoring confidence",
    ],
    tradeOffs: [
      "Slower initial development",
      "Requires discipline",
    ],
    commonMistakes: [
      "Testing implementation instead of behavior",
      "Skipping refactor step",
    ],
  },
};

// ---------------------------------------------------------------------------
// Intent-to-pattern and domain-to-pattern maps for suggestions
// ---------------------------------------------------------------------------

const INTENT_PATTERN_MAP: Record<string, string[]> = {
  implement: ["Factory", "Builder-Pattern", "Strategy"],
  refactor: ["Refactor-Safe", "Extract-Method"],
  debug: ["Debug-Systematic", "Error-First-Handling"],
  test: ["TDD", "Mock-Pattern"],
};

const DOMAIN_PATTERN_MAP: Record<string, string[]> = {
  api: ["REST-API-Design", "Adapter", "Repository"],
  database: ["Repository", "DAO"],
  async: ["Async-Pattern", "Observer"],
  web: ["MVC", "REST-API-Design"],
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Check if `subsequence` appears as a contiguous slice inside `sequence`.
 */
function containsSubsequence(
  sequence: string[],
  subsequence: string[]
): boolean {
  const subLen = subsequence.length;
  for (let i = 0; i <= sequence.length - subLen; i++) {
    let match = true;
    for (let j = 0; j < subLen; j++) {
      if (sequence[i + j] !== subsequence[j]) {
        match = false;
        break;
      }
    }
    if (match) return true;
  }
  return false;
}

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

/**
 * Create a design pattern detector that identifies architectural, coding,
 * and workflow patterns from tool sequences and file contents.
 *
 * @returns Object with pattern detection methods
 */
export function createDesignPatternDetector(): {
  detectWorkflowPattern(
    toolSequence: string[],
    sessionContext?: Record<string, unknown>
  ): DesignPattern | null;
  detectPatternsFromFiles(
    filePaths: string[],
    fileContents: Map<string, string>
  ): DesignPattern[];
  getPatternContext(patternName: string): PatternContext | null;
  suggestPatternsForContext(
    intent: string,
    problemDomain: string
  ): Array<{ pattern: string; relevance: number }>;
} {
  /**
   * Detect a workflow pattern from the given tool usage sequence.
   *
   * @param toolSequence - Ordered list of tool names used in a session
   * @param sessionContext - Optional context map from the session analyzer
   * @returns A DesignPattern if a workflow pattern was detected, else null
   */
  function detectWorkflowPattern(
    toolSequence: string[],
    sessionContext?: Record<string, unknown>
  ): DesignPattern | null {
    if (toolSequence.length === 0) return null;

    for (const [patternName, patternInfo] of Object.entries(
      WORKFLOW_PATTERNS
    )) {
      if (!containsSubsequence(toolSequence, patternInfo.toolSequence)) {
        continue;
      }

      // Base confidence for a sequence match
      let confidence = 0.7;

      if (sessionContext) {
        const contextText = JSON.stringify(sessionContext).toLowerCase();
        const matchingIndicators = patternInfo.indicators.filter((ind) =>
          contextText.includes(ind)
        );
        if (matchingIndicators.length > 0) {
          confidence = Math.min(
            0.95,
            confidence + 0.05 * matchingIndicators.length
          );
        }
      }

      return {
        patternId: `workflow-${patternName.toLowerCase()}`,
        patternType: "workflow",
        patternName,
        confidence,
        description: patternInfo.description,
        indicators: [
          `Tool sequence: ${patternInfo.toolSequence.join(" -> ")}`,
        ],
        affectedFiles: [],
        codeExamples: [],
        metadata: { toolSequence },
      };
    }

    return null;
  }

  /**
   * Detect architectural and coding patterns from file paths and contents.
   *
   * Checks both ARCHITECTURAL_PATTERNS and CODING_PATTERNS against the
   * file paths (by name) and file contents (by indicator substring search).
   *
   * @param filePaths - List of file paths to inspect
   * @param fileContents - Map from file path to source content
   * @returns List of detected DesignPattern objects sorted by confidence desc
   */
  function detectPatternsFromFiles(
    filePaths: string[],
    fileContents: Map<string, string>
  ): DesignPattern[] {
    const patterns: DesignPattern[] = [];

    // --- Architectural patterns (check file paths) ---
    for (const [patternName, patternInfo] of Object.entries(
      ARCHITECTURAL_PATTERNS
    )) {
      const indicatorsFound: string[] = [];
      const affectedFiles: string[] = [];

      for (const filePath of filePaths) {
        const pathLower = filePath.toLowerCase();
        for (const indicator of patternInfo.indicators) {
          if (pathLower.includes(indicator)) {
            indicatorsFound.push(`Path: ${filePath}`);
            affectedFiles.push(filePath);
          }
        }
      }

      // Also check file contents
      for (const [filePath, content] of fileContents) {
        const contentLower = content.toLowerCase();
        for (const indicator of patternInfo.indicators) {
          if (contentLower.includes(indicator)) {
            indicatorsFound.push(
              `Found '${indicator}' in ${filePath.split("/").pop() ?? filePath}`
            );
            if (!affectedFiles.includes(filePath)) {
              affectedFiles.push(filePath);
            }
          }
        }
      }

      if (indicatorsFound.length > 0) {
        const confidence = Math.min(
          1.0,
          indicatorsFound.length / (patternInfo.indicators.length * 2)
        );
        if (confidence >= patternInfo.minConfidence) {
          patterns.push({
            patternId: `arch-${patternName.toLowerCase()}`,
            patternType: "architectural",
            patternName,
            confidence,
            description: patternInfo.description,
            indicators: indicatorsFound.slice(0, 10),
            affectedFiles: [...new Set(affectedFiles)].slice(0, 10),
            codeExamples: [],
            metadata: {},
          });
        }
      }
    }

    // --- Coding patterns (check file contents) ---
    for (const [patternName, patternInfo] of Object.entries(CODING_PATTERNS)) {
      const indicatorsFound: string[] = [];
      const affectedFiles: string[] = [];
      const codeExamples: string[] = [];

      for (const [filePath, content] of fileContents) {
        const contentLower = content.toLowerCase();
        for (const indicator of patternInfo.indicators) {
          if (contentLower.includes(indicator.toLowerCase())) {
            const fileName = filePath.split("/").pop() ?? filePath;
            indicatorsFound.push(`Found '${indicator}' in ${fileName}`);
            affectedFiles.push(filePath);

            // Extract a small code example
            const example = extractCodeExample(content, indicator);
            if (example) {
              codeExamples.push(example);
            }
          }
        }
      }

      if (indicatorsFound.length > 0) {
        const confidence = Math.min(
          1.0,
          indicatorsFound.length / (patternInfo.indicators.length * 3)
        );
        if (confidence >= patternInfo.minConfidence) {
          patterns.push({
            patternId: `code-${patternName.toLowerCase()}`,
            patternType: "coding",
            patternName,
            confidence,
            description: patternInfo.description,
            indicators: indicatorsFound.slice(0, 10),
            affectedFiles: [...new Set(affectedFiles)].slice(0, 10),
            codeExamples: codeExamples.slice(0, 3),
            metadata: {},
          });
        }
      }
    }

    // Sort by confidence descending
    patterns.sort((a, b) => b.confidence - a.confidence);
    return patterns;
  }

  /**
   * Extract a small code example around the first occurrence of an indicator.
   */
  function extractCodeExample(
    source: string,
    indicator: string,
    contextLines: number = 3
  ): string | null {
    const lines = source.split("\n");
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].toLowerCase().includes(indicator.toLowerCase())) {
        const start = Math.max(0, i - contextLines);
        const end = Math.min(lines.length, i + contextLines + 1);
        const example = lines.slice(start, end).join("\n");
        return example.slice(0, 200);
      }
    }
    return null;
  }

  /**
   * Get contextual information about when to use a pattern.
   *
   * @param patternName - Name of the pattern (e.g. "MVC", "TDD", "Repository")
   * @returns PatternContext with usage guidance, or null if unknown
   */
  function getPatternContext(patternName: string): PatternContext | null {
    return PATTERN_CONTEXTS[patternName] ?? null;
  }

  /**
   * Suggest relevant patterns based on intent and problem domain.
   *
   * Scores patterns by matching against intent and domain keyword maps,
   * deduplicates, and returns sorted by relevance descending.
   *
   * @param intent - User intent (e.g. "implement", "refactor")
   * @param problemDomain - Problem domain (e.g. "api", "database")
   * @returns Array of {pattern, relevance} objects sorted by relevance
   */
  function suggestPatternsForContext(
    intent: string,
    problemDomain: string
  ): Array<{ pattern: string; relevance: number }> {
    const suggestions = new Map<string, number>();

    const intentLower = intent.toLowerCase();
    const domainLower = problemDomain.toLowerCase();

    // Match intents
    for (const [intentKey, patterns] of Object.entries(INTENT_PATTERN_MAP)) {
      if (intentLower.includes(intentKey)) {
        for (const pattern of patterns) {
          const existing = suggestions.get(pattern) ?? 0;
          suggestions.set(pattern, Math.max(existing, 0.8));
        }
      }
    }

    // Match domains
    for (const [domainKey, patterns] of Object.entries(DOMAIN_PATTERN_MAP)) {
      if (domainLower.includes(domainKey)) {
        for (const pattern of patterns) {
          const existing = suggestions.get(pattern) ?? 0;
          suggestions.set(pattern, Math.max(existing, 0.7));
        }
      }
    }

    // Sort by relevance descending
    return [...suggestions.entries()]
      .map(([pattern, relevance]) => ({ pattern, relevance }))
      .sort((a, b) => b.relevance - a.relevance);
  }

  return {
    detectWorkflowPattern,
    detectPatternsFromFiles,
    getPatternContext,
    suggestPatternsForContext,
  };
}
