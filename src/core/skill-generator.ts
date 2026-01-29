/**
 * Skill Generator - Enhanced v2 with rich metadata and contextual understanding.
 *
 * Generates SKILL.md files with:
 * - V1: Tool patterns, confidence, execution context
 * - V2: Session analysis, code structure, design patterns, problem-solving approaches
 *
 * Ported from Python core/skill_generator.py (~630 lines).
 */

import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import yaml from "yaml";

import { sanitizeName, isPathSafe } from "./path-security";
import { writeFileAtomic } from "../util/atomic-write";
import type { DetectedPattern, SkillCandidate } from "../types";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Map tool names to human-readable step descriptions (V1). */
const TOOL_STEP_TEMPLATES: Record<string, string> = {
  Read: "Read the file to understand its contents",
  Write: "Create/update the file with the required content",
  Edit: "Edit the file to make the necessary changes",
  Bash: "Run the required command",
  Grep: "Search for patterns in the codebase",
  Glob: "Find files matching the pattern",
  WebFetch: "Fetch content from the URL",
  WebSearch: "Search the web for information",
  Task: "Delegate to a specialized agent",
};

/** Tools that only read state (V1). */
const READ_ONLY_TOOLS = new Set(["Read", "Grep", "Glob", "WebFetch", "WebSearch"]);

/** Tools that mutate state (V1). */
const MUTATING_TOOLS = new Set(["Write", "Edit", "Bash", "NotebookEdit"]);

/** Tools that delegate work (V1). */
const DELEGATION_TOOLS = new Set(["Task"]);

/** Tools that suggest running in a fork / isolated context (V1). */
const FORK_SUGGESTING_TOOLS = new Set(["Bash", "Task"]);

/**
 * Heuristic mapping from tool-set combinations to recommended agent types (V1).
 *
 * Keys are serialised sorted tool arrays (since JS has no frozenset).
 */
const AGENT_TYPE_HEURISTICS: Array<{ tools: Set<string>; agentType: string }> = [
  { tools: new Set(["Read", "Grep"]), agentType: "Explore" },
  { tools: new Set(["Read", "Glob"]), agentType: "Explore" },
  { tools: new Set(["Grep", "Glob"]), agentType: "Explore" },
  { tools: new Set(["Grep", "Read", "Glob"]), agentType: "Explore" },
  { tools: new Set(["Read", "Task"]), agentType: "Plan" },
];

/** Context descriptions for known design patterns. */
const PATTERN_CONTEXTS: Record<string, { when: string; benefits: string[] }> = {
  MVC: {
    when: "Building web applications with clear separation",
    benefits: ["Separates concerns", "Easier testing"],
  },
  Repository: {
    when: "Abstracting data access layer",
    benefits: ["Decouples business logic", "Testable"],
  },
  TDD: {
    when: "Building new features or fixing bugs",
    benefits: ["Better coverage", "Refactoring confidence"],
  },
  "Refactor-Safe": {
    when: "Improving code without changing behavior",
    benefits: ["Maintains tests", "Reduces risk"],
  },
  Factory: {
    when: "Creating objects with complex initialization",
    benefits: ["Centralized creation", "Flexible"],
  },
};

/** Default output directory for auto-generated skills. */
const DEFAULT_OUTPUT_DIR = path.join(os.homedir(), ".claude", "skills", "auto");

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/** Check if every element of `sub` is in `superset`. */
function isSubsetOf(sub: Set<string>, superset: Set<string>): boolean {
  for (const item of sub) {
    if (!superset.has(item)) return false;
  }
  return true;
}

/** Check if two sets share at least one element. */
function setsIntersect(a: Set<string>, b: Set<string>): boolean {
  for (const item of a) {
    if (b.has(item)) return true;
  }
  return false;
}

/** Check if two sets are equal. */
function setsEqual(a: Set<string>, b: Set<string>): boolean {
  if (a.size !== b.size) return false;
  return isSubsetOf(a, b);
}

// ---------------------------------------------------------------------------
// V1 helpers
// ---------------------------------------------------------------------------

/**
 * Determine if the skill should run in an isolated (fork) context.
 *
 * Returns true when the tool sequence contains tools with side effects
 * that benefit from isolation (e.g. Bash, Task).
 */
function shouldUseFork(tools: string[]): boolean {
  return setsIntersect(new Set(tools), FORK_SUGGESTING_TOOLS);
}

/**
 * Determine the recommended agent type from the tool set.
 *
 * Uses heuristic matching: exact match first, then subset match,
 * then falls back to read-only / delegation / null.
 */
function determineAgentType(tools: string[]): string | null {
  const toolSet = new Set(tools);

  // Exact match
  for (const h of AGENT_TYPE_HEURISTICS) {
    if (setsEqual(toolSet, h.tools)) {
      return h.agentType;
    }
  }

  // Subset match (toolSet is a subset of heuristic tools)
  for (const h of AGENT_TYPE_HEURISTICS) {
    if (isSubsetOf(toolSet, h.tools)) {
      return h.agentType;
    }
  }

  if (isSubsetOf(toolSet, READ_ONLY_TOOLS)) {
    return "Explore";
  }
  if (toolSet.has("Task")) {
    return "general-purpose";
  }

  return null;
}

/** Generate a unique list of allowed tools, preserving first-seen order. */
function generateAllowedTools(tools: string[]): string[] {
  const seen = new Set<string>();
  const unique: string[] = [];
  for (const tool of tools) {
    if (!seen.has(tool)) {
      seen.add(tool);
      unique.push(tool);
    }
  }
  return unique;
}

/**
 * Generate tags for Vercel skills.sh compatibility.
 *
 * Combines tool tags, intent tags, mental-domain tags, and design-pattern
 * tags, capped at 10 for readability.
 */
function generateTags(pattern: DetectedPattern): string[] {
  const tags: string[] = [];

  // Tool-based tags
  for (const tool of pattern.toolSequence) {
    const tag = tool.toLowerCase().replace(/_/g, "-");
    if (!tags.includes(tag)) {
      tags.push(tag);
    }
  }

  // Intent-based tags from session context
  if (pattern.sessionContext) {
    const ctx = pattern.sessionContext as Record<string, unknown>;
    if (ctx.primary_intent) {
      tags.push(String(ctx.primary_intent));
    }
    if (ctx.workflow_type) {
      const workflow = String(ctx.workflow_type).toLowerCase().replace(/_/g, "-");
      if (!tags.includes(workflow)) {
        tags.push(workflow);
      }
    }
  }

  // Mental domain tags
  if (pattern.mentalContext) {
    const mc = pattern.mentalContext as Record<string, unknown>;
    const domains = (mc.domains ?? []) as Array<Record<string, unknown>>;
    for (const domain of domains.slice(0, 3)) {
      const domainTag = String(domain.name).toLowerCase().replace(/ /g, "-");
      if (!tags.includes(domainTag)) {
        tags.push(domainTag);
      }
    }
  }

  // Design pattern tags
  if (pattern.designPatterns) {
    for (const dp of pattern.designPatterns.slice(0, 2)) {
      const patternTag = String(dp.name).toLowerCase().replace(/ /g, "-");
      if (!tags.includes(patternTag)) {
        tags.push(patternTag);
      }
    }
  }

  return tags.slice(0, 10);
}

/**
 * Generate a sanitized, spec-compliant kebab-case skill name.
 *
 * Appends the first 6 chars of the pattern ID as a uniqueness suffix.
 */
function generateSkillName(pattern: DetectedPattern): string {
  let rawName: string;
  if (pattern.suggestedName) {
    rawName = pattern.suggestedName;
  } else {
    const tools = pattern.toolSequence;
    if (tools.length >= 2) {
      rawName = `${tools[0].toLowerCase()}-${tools[tools.length - 1].toLowerCase()}-workflow`;
    } else {
      rawName = tools.length > 0 ? `${tools[0].toLowerCase()}-workflow` : "auto-workflow";
    }
  }

  rawName = `${rawName}-${pattern.id.slice(0, 6)}`;
  return sanitizeName(rawName);
}

/** Generate a human-readable description for the pattern. */
function generateDescription(pattern: DetectedPattern): string {
  if (pattern.suggestedDescription) {
    return pattern.suggestedDescription;
  }
  const tools = pattern.toolSequence;
  if (tools.length === 2) {
    return `Workflow: ${tools[0]} then ${tools[1]}`;
  }
  if (tools.length > 2) {
    return `Workflow: ${tools.join(" \u2192 ")}`;
  }
  return "Auto-detected workflow";
}

/** Generate numbered procedural steps from the tool sequence. */
function generateSteps(pattern: DetectedPattern): string[] {
  return pattern.toolSequence.map((tool, i) => {
    const desc = TOOL_STEP_TEMPLATES[tool] ?? `Use ${tool} tool`;
    return `${i + 1}. ${desc}`;
  });
}

// ---------------------------------------------------------------------------
// V2 content builders
// ---------------------------------------------------------------------------

/** Build the Context section markdown. */
function buildContextSection(pattern: DetectedPattern): string {
  const lines: string[] = ["## Context\n"];

  if (pattern.sessionContext) {
    const ctx = pattern.sessionContext as Record<string, unknown>;
    lines.push("This workflow is most appropriate when:\n");

    if (ctx.primary_intent) {
      const intentDescs: Record<string, string> = {
        debug: "tracking down and fixing bugs",
        implement: "building new features",
        refactor: "improving code structure",
        test: "writing or improving tests",
        explore: "understanding existing code",
        document: "adding documentation",
      };
      const desc = intentDescs[String(ctx.primary_intent)] ?? String(ctx.primary_intent);
      lines.push(`- You are ${desc}\n`);
    }

    if (ctx.problem_domains) {
      const domains = (ctx.problem_domains as string[]).slice(0, 3).join(", ");
      lines.push(`- Working in these areas: ${domains}\n`);
    }

    if (ctx.workflow_type) {
      lines.push(`- Following a ${String(ctx.workflow_type)} approach\n`);
    }

    if (ctx.tool_success_rate) {
      const rate = Math.round(Number(ctx.tool_success_rate) * 100);
      lines.push(`\nSuccess rate in previous usage: ${rate}%\n`);
    }
  }

  return lines.join("");
}

/** Build the Detected Patterns section markdown. */
function buildPatternsSection(pattern: DetectedPattern): string {
  if (!pattern.designPatterns || pattern.designPatterns.length === 0) {
    return "";
  }

  const lines: string[] = ["## Detected Patterns\n"];
  lines.push("This workflow incorporates these design patterns:\n\n");

  for (const dp of pattern.designPatterns.slice(0, 3)) {
    const name = String(dp.name ?? "Unknown");
    const confidence = Math.round(Number(dp.confidence ?? 0) * 100);
    const desc = dp.description ? String(dp.description) : "";
    const patternType = dp.type ? String(dp.type) : "";

    lines.push(`### ${name} (${patternType}, confidence: ${confidence}%)\n`);
    if (desc) {
      lines.push(`- **Description:** ${desc}\n`);
    }

    const context = PATTERN_CONTEXTS[name];
    if (context) {
      lines.push(`- **When to use:** ${context.when}\n`);
      if (context.benefits.length > 0) {
        lines.push(`- **Benefits:** ${context.benefits.slice(0, 2).join(", ")}\n`);
      }
    }

    const indicators = dp.indicators as string[] | undefined;
    if (indicators && indicators.length > 0) {
      lines.push(`- **Detected from:** ${indicators[0]}\n`);
    }

    lines.push("\n");
  }

  return lines.join("");
}

/** Build the Code Structure Awareness section markdown. */
function buildCodeStructureSection(pattern: DetectedPattern): string {
  if (!pattern.codeContext) {
    return "";
  }

  const lines: string[] = ["## Code Structure Awareness\n"];
  const ctx = pattern.codeContext as Record<string, unknown>;

  if (ctx.detected_symbols) {
    const symbols = ctx.detected_symbols as Record<string, unknown>;

    if (symbols.classes) {
      lines.push("**Key Classes:**\n");
      const classes = (symbols.classes as Array<Record<string, unknown>>).slice(0, 5);
      for (const cls of classes) {
        lines.push(`- \`${cls.name}\` (${cls.file}:${cls.line})\n`);
      }
      lines.push("\n");
    }

    if (symbols.functions) {
      lines.push("**Key Functions:**\n");
      const funcs = (symbols.functions as Array<Record<string, unknown>>).slice(0, 5);
      for (const func of funcs) {
        lines.push(`- \`${func.name}\` (${func.file}:${func.line})\n`);
      }
      lines.push("\n");
    }
  }

  if (ctx.dependencies) {
    lines.push("**Dependencies:**\n");
    const deps = (ctx.dependencies as Array<Record<string, unknown>>).slice(0, 3);
    for (const dep of deps) {
      lines.push(`- ${dep.source} \u2192 ${dep.target} (${dep.type})\n`);
    }
    lines.push("\n");
  }

  return lines.join("");
}

/** Build enhanced steps incorporating the problem-solving approach. */
function buildEnhancedSteps(pattern: DetectedPattern): string[] {
  const approach = pattern.problemSolvingApproach as Record<string, unknown> | null | undefined;
  if (!approach || !approach.steps) {
    return generateSteps(pattern);
  }

  const approachSteps = (approach.steps as string[]).slice(0, 6);
  return approachSteps.map((step, i) => {
    let toolHint = "";
    if (i < pattern.toolSequence.length) {
      toolHint = ` (${pattern.toolSequence[i]})`;
    }
    return `${i + 1}. ${step}${toolHint}`;
  });
}

/**
 * Build v2 content sections from session/code/design-pattern context.
 *
 * Returns null when no v2-relevant metadata is present.
 */
function buildV2Content(pattern: DetectedPattern): Record<string, unknown> | null {
  if (!pattern.sessionContext && !pattern.codeContext && !pattern.designPatterns) {
    return null;
  }

  const content: Record<string, unknown> = {};

  if (pattern.sessionContext || pattern.designPatterns) {
    content.context_section = buildContextSection(pattern);
  }

  if (pattern.designPatterns) {
    content.patterns_section = buildPatternsSection(pattern);
  }

  if (pattern.codeContext) {
    content.code_structure_section = buildCodeStructureSection(pattern);
  }

  if (pattern.problemSolvingApproach) {
    content.enhanced_steps = buildEnhancedSteps(pattern);
  }

  return Object.keys(content).length > 0 ? content : null;
}

/**
 * Build the full YAML frontmatter object with v1 + v2 + hybrid metadata.
 */
function buildFrontmatter(
  pattern: DetectedPattern,
  name: string,
  description: string,
  useFork: boolean,
  agentType: string | null,
  allowedTools: string[],
): Record<string, unknown> {
  const fm: Record<string, unknown> = {
    name,
    description: description.slice(0, 1024), // Spec max 1024 chars
    version: "1.0.0",
  };

  if (useFork) {
    fm.context = "fork";
    if (agentType) {
      fm.agent = agentType;
    }
  }

  if (allowedTools.length > 0) {
    fm["allowed-tools"] = [...allowedTools];
  }

  // V1 metadata
  fm["auto-generated"] = true;
  fm.confidence = Math.round(pattern.confidence * 100) / 100;
  fm["occurrence-count"] = pattern.occurrenceCount;
  fm["source-sessions"] = pattern.sessionIds.slice(0, 5);
  fm["first-seen"] = pattern.firstSeen;
  fm["last-seen"] = pattern.lastSeen;
  fm["pattern-id"] = pattern.id;
  fm["created-at"] = new Date().toISOString();

  // V2 metadata
  if (pattern.sessionContext) {
    fm["session-analysis"] = pattern.sessionContext;
  }

  if (pattern.codeContext) {
    const cc = pattern.codeContext as Record<string, unknown>;
    fm["code-context"] = {
      analyzed_files: cc.analyzed_files ?? 0,
      primary_languages: cc.primary_languages ?? [],
    };
  }

  if (pattern.designPatterns) {
    fm["design-patterns"] = pattern.designPatterns;
  }

  if (pattern.problemSolvingApproach) {
    const psa = pattern.problemSolvingApproach as Record<string, unknown>;
    fm["problem-solving-approach"] = {
      type: psa.type ?? null,
      description: psa.description ?? null,
    };
  }

  // Hybrid Phase 3: Mental context
  if (pattern.mentalContext) {
    const mc = pattern.mentalContext as Record<string, unknown>;
    const domains = (mc.domains ?? []) as Array<Record<string, unknown>>;
    const capabilities = (mc.capabilities ?? []) as Array<Record<string, unknown>>;
    const aspects = (mc.aspects ?? []) as Array<Record<string, unknown>>;
    fm["mental-context"] = {
      domains: domains.map((d) => String(d.name)),
      capabilities: capabilities.map((c) => String(c.name)),
      aspects: aspects.map((a) => String(a.name)),
    };
  }

  // Vercel skills.sh compatibility metadata
  fm["compatible-agents"] = ["claude-code", "opencode", "codex"];
  fm.tags = generateTags(pattern);
  fm.source = "auto-generated";
  fm["derived-from"] = "local-patterns";

  return fm;
}

// ---------------------------------------------------------------------------
// Public factory
// ---------------------------------------------------------------------------

/**
 * Create a skill generator instance.
 *
 * Uses the factory-function pattern (no classes) following project conventions.
 *
 * @param outputDir - Directory for saving generated skills.
 *   Defaults to `~/.claude/skills/auto`.
 * @returns An object with skill generation, rendering, listing, and deletion methods.
 */
export function createSkillGenerator(outputDir?: string): {
  generateCandidate(
    pattern: DetectedPattern,
    options?: {
      forceFork?: boolean;
      forceAgent?: string;
      customAllowedTools?: string[];
    },
  ): SkillCandidate;

  saveSkill(
    candidate: SkillCandidate,
    options?: {
      updateLockFile?: boolean;
      createSymlinks?: boolean;
    },
  ): string;

  renderSkillMd(params: {
    name: string;
    description: string;
    steps: string[];
    frontmatter: Record<string, unknown>;
    v2Content?: Record<string, unknown> | null;
  }): string;

  listGeneratedSkills(): string[];
  deleteSkill(name: string): boolean;
} {
  const outDir = outputDir ?? DEFAULT_OUTPUT_DIR;

  // ------------------------------------------------------------------
  // renderSkillMd
  // ------------------------------------------------------------------

  /**
   * Render a complete SKILL.md string from its parts.
   *
   * @param params - Skill name, description, steps, frontmatter, and optional v2 content.
   * @returns The formatted SKILL.md content.
   */
  function renderSkillMd(params: {
    name: string;
    description: string;
    steps: string[];
    frontmatter: Record<string, unknown>;
    v2Content?: Record<string, unknown> | null;
  }): string {
    const yamlContent = yaml.stringify(params.frontmatter, {
      defaultKeyType: "PLAIN",
      defaultStringType: "PLAIN",
    }).trim();

    let content = `---\n${yamlContent}\n---\n\n# ${params.name}\n\n${params.description}\n\n`;

    // V2: context sections
    if (params.v2Content) {
      if (params.v2Content.context_section) {
        content += String(params.v2Content.context_section) + "\n";
      }
      if (params.v2Content.patterns_section) {
        content += String(params.v2Content.patterns_section) + "\n";
      }
    }

    // Steps (possibly enhanced with v2)
    const stepsToUse = params.v2Content?.enhanced_steps
      ? (params.v2Content.enhanced_steps as string[])
      : params.steps;

    content += "## Steps\n\n";
    content += stepsToUse.join("\n");
    content += "\n\n";

    // V2: code structure section
    if (params.v2Content?.code_structure_section) {
      content += String(params.v2Content.code_structure_section) + "\n";
    }

    // Footer
    content += `## Generated by Auto-Skill v2\n\nThis skill was automatically detected from your usage patterns.\nConfidence reflects how frequently and successfully this pattern was used.\n`;

    return content;
  }

  // ------------------------------------------------------------------
  // generateCandidate
  // ------------------------------------------------------------------

  /**
   * Generate a skill candidate from a detected pattern (v1 + v2).
   *
   * @param pattern - The detected workflow pattern.
   * @param options - Optional overrides for fork, agent type, and allowed tools.
   * @returns A SkillCandidate ready for user review and saving.
   */
  function generateCandidate(
    pattern: DetectedPattern,
    options?: {
      forceFork?: boolean;
      forceAgent?: string;
      customAllowedTools?: string[];
    },
  ): SkillCandidate {
    const tools = pattern.toolSequence;

    // V1: Generate base info
    const name = generateSkillName(pattern);
    const description = generateDescription(pattern);
    const steps = generateSteps(pattern);

    // V1: Determine execution context
    const useFork =
      options?.forceFork !== undefined ? options.forceFork : shouldUseFork(tools);
    const agentType =
      options?.forceAgent !== undefined ? options.forceAgent : determineAgentType(tools);
    const allowedTools =
      options?.customAllowedTools !== undefined
        ? options.customAllowedTools
        : generateAllowedTools(tools);

    // V1: Build frontmatter
    const frontmatter = buildFrontmatter(
      pattern,
      name,
      description,
      useFork,
      agentType,
      allowedTools,
    );

    // V2: Add enhanced content sections
    const v2Content = pattern.sessionContext ? buildV2Content(pattern) : null;

    const outputPath = path.join(outDir, name, "SKILL.md");

    return {
      pattern,
      name,
      description,
      steps,
      outputPath,
      yamlFrontmatter: frontmatter,
      useFork,
      agentType,
      allowedTools,
      v2Content,
    };
  }

  // ------------------------------------------------------------------
  // saveSkill
  // ------------------------------------------------------------------

  /**
   * Save a skill candidate to disk.
   *
   * Validates path safety to prevent path-traversal attacks, writes
   * atomically, and optionally updates the lock file.
   *
   * @param candidate - The skill candidate to save.
   * @param options - Optional flags for lock-file update and symlink creation.
   * @returns The absolute path to the saved SKILL.md file.
   * @throws {Error} If the output path is outside the allowed output directory.
   */
  function saveSkill(
    candidate: SkillCandidate,
    options?: {
      updateLockFile?: boolean;
      createSymlinks?: boolean;
    },
  ): string {
    const candidatePath = candidate.outputPath;
    const resolvedOut = path.resolve(outDir);

    // Ensure the output directory exists before safety check
    fs.mkdirSync(resolvedOut, { recursive: true });

    // Ensure the skill sub-directory exists so realpath can resolve
    const skillDir = path.dirname(candidatePath);
    fs.mkdirSync(skillDir, { recursive: true });

    if (!isPathSafe(candidatePath, resolvedOut)) {
      throw new Error(
        `Unsafe skill path: ${candidatePath} is not within ${resolvedOut}`,
      );
    }

    const content = renderSkillMd({
      name: candidate.name,
      description: candidate.description,
      steps: candidate.steps,
      frontmatter: candidate.yamlFrontmatter,
      v2Content: candidate.v2Content,
    });

    writeFileAtomic(candidatePath, content);

    // Lock file update is best-effort
    if (options?.updateLockFile !== false) {
      try {
        // Lazy-load to avoid circular dependencies at module level
        // eslint-disable-next-line @typescript-eslint/no-require-imports
        const lockMod = require("./lock-file");
        if (lockMod && typeof lockMod.createLockFile === "function") {
          const lock = lockMod.createLockFile();
          lock.load();
          lock.addSkill({
            name: candidate.name,
            path: candidatePath,
            content,
            source: "auto",
          });
          lock.save();
        }
      } catch {
        // Lock file update is best-effort
      }
    }

    // Create symlinks to other installed agents
    if (options?.createSymlinks) {
      try {
        // eslint-disable-next-line @typescript-eslint/no-require-imports
        const registryMod = require("./agent-registry");
        if (registryMod && typeof registryMod.createAgentRegistry === "function") {
          const registry = registryMod.createAgentRegistry();
          const current = registry.detectCurrentAgent();
          registry.createSkillSymlinks(
            candidatePath,
            candidate.name,
            current?.id ?? undefined,
          );
        }
      } catch {
        // Symlink creation is best-effort
      }
    }

    return candidatePath;
  }

  // ------------------------------------------------------------------
  // listGeneratedSkills
  // ------------------------------------------------------------------

  /**
   * List all auto-generated skill file paths.
   *
   * Scans the output directory for sub-directories containing a SKILL.md file.
   *
   * @returns Sorted array of absolute paths to SKILL.md files.
   */
  function listGeneratedSkills(): string[] {
    const resolved = path.resolve(outDir);
    if (!fs.existsSync(resolved)) {
      return [];
    }

    const skills: string[] = [];
    const entries = fs.readdirSync(resolved, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isDirectory()) {
        const skillFile = path.join(resolved, entry.name, "SKILL.md");
        if (fs.existsSync(skillFile)) {
          skills.push(skillFile);
        }
      }
    }

    return skills.sort();
  }

  // ------------------------------------------------------------------
  // deleteSkill
  // ------------------------------------------------------------------

  /**
   * Delete an auto-generated skill by name.
   *
   * Validates that the resolved skill path is within the output directory
   * to prevent directory-traversal attacks.
   *
   * @param name - The skill name (directory name inside the output dir).
   * @returns True if the skill was deleted, false otherwise.
   */
  function deleteSkill(name: string): boolean {
    const resolved = path.resolve(outDir);
    const skillPath = path.resolve(resolved, name);

    // Safety: ensure we are not escaping the output directory
    if (!skillPath.startsWith(resolved + path.sep) && skillPath !== resolved) {
      return false;
    }

    if (fs.existsSync(skillPath) && fs.statSync(skillPath).isDirectory()) {
      fs.rmSync(skillPath, { recursive: true, force: true });
      return true;
    }

    return false;
  }

  return {
    generateCandidate,
    saveSkill,
    renderSkillMd,
    listGeneratedSkills,
    deleteSkill,
  };
}
