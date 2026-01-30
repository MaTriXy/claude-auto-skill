#!/usr/bin/env node
/**
 * Observer Hook - Captures tool usage events and triggers pattern detection.
 *
 * Called by Claude Code via PostToolUse and Stop hooks.
 * IMPORTANT: Never throw errors. Always exit 0 (graceful degradation).
 */
import { createEventStore } from "../core/event-store";
import { createAgentRegistry } from "../core/agent-registry";

/** Retrieve the current Claude session ID from the environment. */
function getSessionId(): string {
  return process.env.CLAUDE_SESSION_ID || "unknown";
}

/** Retrieve the current project path from the environment. */
function getProjectPath(): string {
  return process.env.CLAUDE_PROJECT_DIR || process.cwd();
}

/** Detect the current coding agent using the agent registry. */
function getAgentId(): string {
  const registry = createAgentRegistry();
  const agent = registry.detectCurrentAgent();
  return agent?.id || "unknown";
}

/**
 * Parse hook input from stdin (JSON).
 * Reads synchronously since hooks are short-lived processes.
 */
function parseHookInput(): Record<string, unknown> {
  try {
    const chunks: Buffer[] = [];
    const fs = require("node:fs");
    const fd = fs.openSync("/dev/stdin", "r");
    const buf = Buffer.alloc(65536);
    let n: number;
    try {
      while ((n = fs.readSync(fd, buf)) > 0) {
        chunks.push(buf.subarray(0, n));
      }
    } catch {
      /* EOF */
    }
    fs.closeSync(fd);
    const input = Buffer.concat(chunks).toString("utf8").trim();
    if (!input) return {};
    return JSON.parse(input);
  } catch {
    return {};
  }
}

/**
 * Record a tool usage event from a PostToolUse hook.
 * Parses stdin for tool name, input, and response, then stores the event.
 */
function recordEvent(): void {
  const hookInput = parseHookInput();
  const toolName = hookInput.tool_name as string | undefined;
  if (!toolName) return;

  // Skip self-referential events to avoid infinite loops
  if (toolName.toLowerCase().includes("auto-skill")) return;

  const store = createEventStore();
  const toolInput =
    typeof hookInput.tool_input === "object"
      ? (hookInput.tool_input as Record<string, unknown>)
      : {};
  const toolResponse = String(hookInput.tool_response || "");
  const errorKeywords = ["error", "failed", "exception", "traceback"];
  const success = !errorKeywords.some((kw) =>
    toolResponse.toLowerCase().includes(kw),
  );

  store.recordEvent(
    getSessionId(),
    getProjectPath(),
    toolName,
    toolInput,
    toolResponse || undefined,
    success,
    getAgentId(),
  );
}

/**
 * Analyze the current session for patterns.
 * Called by the Stop hook when Claude finishes a conversation turn.
 */
function analyzeSession(): void {
  const store = createEventStore();
  const events = store.getSessionEvents(getSessionId());
  if (!events || events.length === 0) return;

  console.log("\n" + "=".repeat(60));
  console.log("Auto-Skill: Session analysis complete.");
  console.log("Run 'auto-skill discover' to review patterns.");
  console.log("=".repeat(60) + "\n");
}

// Main entry point
const command = process.argv[2];
try {
  if (command === "record") recordEvent();
  else if (command === "analyze") analyzeSession();
} catch {
  // Never throw - graceful degradation
}
process.exit(0);
