/**
 * Telemetry Collector - Tracks skill usage metrics for effectiveness analysis.
 *
 * Records per-skill usage events with timing, outcome, and agent context.
 * Provides aggregation queries for effectiveness reports.
 *
 * Anonymous telemetry follows privacy-first principles:
 * - No PII collected (no usernames, IPs, file paths, or identifying data)
 * - No content capture (no search queries, file contents, or user input)
 * - Aggregate only (counts, timing, scores -- not specific values)
 * - Fire-and-forget (never blocks, silent failures)
 * - Transparent opt-out via environment variables:
 *     export AUTO_SKILL_NO_TELEMETRY=1   (tool-specific)
 *     export DO_NOT_TRACK=1              (universal standard)
 * - Automatically disabled in CI environments
 *
 * Ported from Python core/telemetry.py (~337 lines).
 */

import os from "node:os";
import path from "node:path";
import https from "node:https";
import fs from "node:fs";

import { ulid } from "../util/ulid";
import type { ToolEvent } from "../types";

// ---------------------------------------------------------------------------
// Anonymous telemetry configuration
// ---------------------------------------------------------------------------

/** Telemetry beacon endpoint. */
const TELEMETRY_ENDPOINT = "https://t.insightx.pro";

/** Current telemetry protocol version. */
const TELEMETRY_VERSION = "3.0.2";

/** Tool identifier sent with each beacon. */
const TOOL_ID = "auto-skill";

/** Environment variables that indicate a CI environment. */
const CI_VARS = [
  "CI",
  "GITHUB_ACTIONS",
  "GITLAB_CI",
  "CIRCLECI",
  "TRAVIS",
  "BUILDKITE",
  "JENKINS_URL",
];

// ---------------------------------------------------------------------------
// Telemetry event and report interfaces
// ---------------------------------------------------------------------------

/** A single skill usage telemetry event. */
export interface TelemetryEvent {
  id: string;
  skillId: string;
  skillName: string;
  sessionId: string;
  agentId: string;
  durationMs: number | null;
  outcome: string; // "success" | "failure" | "partial" | "skipped"
  timestamp: string; // ISO-8601
}

/** Aggregated effectiveness data for a skill. */
export interface EffectivenessReport {
  skillName: string;
  totalUses: number;
  successCount: number;
  failureCount: number;
  successRate: number;
  avgDurationMs: number | null;
  agentsUsed: string[];
  lastUsed: string; // ISO-8601
}

// ---------------------------------------------------------------------------
// Anonymous beacon helpers
// ---------------------------------------------------------------------------

/**
 * Check if anonymous telemetry is disabled.
 *
 * Telemetry is disabled when any of the following are true:
 * - AUTO_SKILL_NO_TELEMETRY is set
 * - DO_NOT_TRACK is set (universal standard)
 * - Any CI environment variable is detected
 *
 * @returns True if telemetry should be suppressed.
 */
export function isTelemetryDisabled(): boolean {
  if (process.env.AUTO_SKILL_NO_TELEMETRY) {
    return true;
  }
  if (process.env.DO_NOT_TRACK) {
    return true;
  }
  return CI_VARS.some((v) => !!process.env[v]);
}

/**
 * Fire-and-forget anonymous telemetry beacon.
 *
 * Sends a lightweight GET request to the telemetry endpoint with
 * aggregate data only (no PII). The request is non-blocking and
 * failures are silently ignored.
 *
 * @param event - Event name (e.g. "skill_used", "skill_generated").
 * @param data - Optional aggregate data (counts, timing, scores -- never PII).
 */
export function track(
  event: string,
  data?: Record<string, string | number>,
): void {
  if (isTelemetryDisabled()) {
    return;
  }

  try {
    const params = new URLSearchParams({
      t: TOOL_ID,
      e: event,
      v: TELEMETRY_VERSION,
      node: process.version,
      os: process.platform,
    });

    if (data) {
      for (const [key, value] of Object.entries(data)) {
        params.set(key, String(value));
      }
    }

    const url = `${TELEMETRY_ENDPOINT}?${params.toString()}`;

    // Fire-and-forget: ignore the response entirely
    const req = https.get(url, { timeout: 2000 }, (res) => {
      res.resume(); // Drain the response to free resources
    });
    req.on("error", () => {
      // Silent failure -- telemetry must never surface errors
    });
    req.end();
  } catch {
    // Silent failure
  }
}

// ---------------------------------------------------------------------------
// Database helper
// ---------------------------------------------------------------------------

/** SQL schema for the telemetry table. */
const SCHEMA_SQL = `
CREATE TABLE IF NOT EXISTS skill_telemetry (
  id TEXT PRIMARY KEY,
  skill_id TEXT NOT NULL,
  skill_name TEXT NOT NULL,
  session_id TEXT NOT NULL,
  agent_id TEXT NOT NULL DEFAULT 'unknown',
  duration_ms INTEGER,
  outcome TEXT NOT NULL,
  timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_telemetry_skill
  ON skill_telemetry(skill_id);

CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp
  ON skill_telemetry(timestamp);
`;

/**
 * Lazy-load and initialize the SQLite database.
 *
 * Uses better-sqlite3 (Node) or bun:sqlite (Bun) via the shared
 * db.ts module when available, falling back to a direct require.
 *
 * @param dbPath - Absolute path to the SQLite database file.
 * @returns An initialised database handle.
 */
function getDb(dbPath: string): import("./db").Database {
  // Prefer the shared openDatabase helper
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { openDatabase } = require("./db") as typeof import("./db");
    const db = openDatabase(dbPath);

    // Create the telemetry table (idempotent)
    for (const stmt of SCHEMA_SQL.split(";")) {
      const trimmed = stmt.trim();
      if (trimmed) {
        db.exec(trimmed);
      }
    }

    return db;
  } catch {
    // Fallback: use better-sqlite3 directly
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const Database = require("better-sqlite3");
    const dir = path.dirname(dbPath);
    fs.mkdirSync(dir, { recursive: true });

    const db = new Database(dbPath);
    db.pragma("journal_mode = WAL");
    db.pragma("foreign_keys = ON");

    for (const stmt of SCHEMA_SQL.split(";")) {
      const trimmed = stmt.trim();
      if (trimmed) {
        db.exec(trimmed);
      }
    }

    return db as import("./db").Database;
  }
}

// ---------------------------------------------------------------------------
// Default database path
// ---------------------------------------------------------------------------

/** Default path for the telemetry SQLite database. */
const DEFAULT_DB_PATH = path.join(
  os.homedir(),
  ".claude",
  "auto-skill",
  "telemetry.db",
);

// ---------------------------------------------------------------------------
// Public factory
// ---------------------------------------------------------------------------

/**
 * Create a telemetry collector instance.
 *
 * Records per-skill usage events in a local SQLite database and provides
 * aggregation queries for effectiveness analysis.
 *
 * @param dbPath - Path to the SQLite database file.
 *   Defaults to `~/.claude/auto-skill/telemetry.db`.
 * @returns An object with event recording and reporting methods.
 */
export function createTelemetryCollector(dbPath?: string): {
  recordEvent(params: {
    skillId: string;
    skillName: string;
    sessionId: string;
    outcome: string;
    agentId?: string;
    durationMs?: number;
  }): TelemetryEvent;

  getEffectivenessReport(skillName?: string): EffectivenessReport[];
  getEvents(skillName?: string, limit?: number): TelemetryEvent[];
} {
  const resolvedPath = dbPath ?? DEFAULT_DB_PATH;

  // Lazy-initialised database handle
  let db: import("./db").Database | null = null;

  /** Get or create the database connection. */
  function ensureDb(): import("./db").Database {
    if (!db) {
      db = getDb(resolvedPath);
    }
    return db;
  }

  // ---------------------------------------------------------------
  // recordEvent
  // ---------------------------------------------------------------

  /**
   * Record a skill usage telemetry event.
   *
   * Persists the event to SQLite and fires an anonymous telemetry
   * beacon with aggregate data (outcome, agent, duration).
   *
   * @param params - Event parameters.
   * @returns The recorded TelemetryEvent.
   */
  function recordEvent(params: {
    skillId: string;
    skillName: string;
    sessionId: string;
    outcome: string;
    agentId?: string;
    durationMs?: number;
  }): TelemetryEvent {
    const event: TelemetryEvent = {
      id: ulid(),
      skillId: params.skillId,
      skillName: params.skillName,
      sessionId: params.sessionId,
      agentId: params.agentId ?? "unknown",
      durationMs: params.durationMs ?? null,
      outcome: params.outcome,
      timestamp: new Date().toISOString(),
    };

    const database = ensureDb();
    const stmt = database.prepare(`
      INSERT INTO skill_telemetry
        (id, skill_id, skill_name, session_id, agent_id, duration_ms, outcome, timestamp)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `);
    stmt.run(
      event.id,
      event.skillId,
      event.skillName,
      event.sessionId,
      event.agentId,
      event.durationMs,
      event.outcome,
      event.timestamp,
    );

    // Fire anonymous telemetry (aggregate data only, no PII)
    track("skill_used", {
      outcome: event.outcome,
      agent: event.agentId,
      ms: event.durationMs ?? 0,
    });

    return event;
  }

  // ---------------------------------------------------------------
  // getEffectivenessReport
  // ---------------------------------------------------------------

  /**
   * Get effectiveness reports for skills.
   *
   * Aggregates usage events by skill name, computing success rates,
   * average durations, and unique agent lists.
   *
   * @param skillName - Optional filter to a specific skill.
   * @returns Array of EffectivenessReport objects, sorted by total uses descending.
   */
  function getEffectivenessReport(
    skillName?: string,
  ): EffectivenessReport[] {
    const database = ensureDb();

    let query = `
      SELECT
        skill_name,
        COUNT(*) as total_uses,
        SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) as success_count,
        SUM(CASE WHEN outcome = 'failure' THEN 1 ELSE 0 END) as failure_count,
        AVG(duration_ms) as avg_duration_ms,
        MAX(timestamp) as last_used
      FROM skill_telemetry
    `;
    const params: unknown[] = [];

    if (skillName) {
      query += " WHERE skill_name = ?";
      params.push(skillName);
    }

    query += " GROUP BY skill_name ORDER BY total_uses DESC";

    const rows = database.prepare(query).all(...params) as Array<{
      skill_name: string;
      total_uses: number;
      success_count: number;
      failure_count: number;
      avg_duration_ms: number | null;
      last_used: string;
    }>;

    const reports: EffectivenessReport[] = [];

    for (const row of rows) {
      const total = Number(row.total_uses);
      const success = Number(row.success_count);
      const failure = Number(row.failure_count);
      const successRate = total > 0 ? success / total : 0;

      // Get unique agents for this skill
      const agentRows = database
        .prepare(
          "SELECT DISTINCT agent_id FROM skill_telemetry WHERE skill_name = ?",
        )
        .all(row.skill_name) as Array<{ agent_id: string }>;

      const agentsUsed = agentRows.map((r) => r.agent_id);

      reports.push({
        skillName: row.skill_name,
        totalUses: total,
        successCount: success,
        failureCount: failure,
        successRate: Math.round(successRate * 1000) / 1000,
        avgDurationMs:
          row.avg_duration_ms !== null
            ? Math.round(row.avg_duration_ms)
            : null,
        agentsUsed,
        lastUsed: row.last_used,
      });
    }

    return reports;
  }

  // ---------------------------------------------------------------
  // getEvents
  // ---------------------------------------------------------------

  /**
   * Get raw telemetry events.
   *
   * @param skillName - Optional filter to a specific skill.
   * @param limit - Maximum number of events to return (default 100).
   * @returns Array of TelemetryEvent objects, newest first.
   */
  function getEvents(
    skillName?: string,
    limit = 100,
  ): TelemetryEvent[] {
    const database = ensureDb();

    let query = "SELECT * FROM skill_telemetry";
    const params: unknown[] = [];

    if (skillName) {
      query += " WHERE skill_name = ?";
      params.push(skillName);
    }

    query += " ORDER BY timestamp DESC LIMIT ?";
    params.push(limit);

    const rows = database.prepare(query).all(...params) as Array<{
      id: string;
      skill_id: string;
      skill_name: string;
      session_id: string;
      agent_id: string;
      duration_ms: number | null;
      outcome: string;
      timestamp: string;
    }>;

    return rows.map((row) => ({
      id: row.id,
      skillId: row.skill_id,
      skillName: row.skill_name,
      sessionId: row.session_id,
      agentId: row.agent_id,
      durationMs: row.duration_ms,
      outcome: row.outcome,
      timestamp: row.timestamp,
    }));
  }

  return {
    recordEvent,
    getEffectivenessReport,
    getEvents,
  };
}
