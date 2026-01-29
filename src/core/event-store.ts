/**
 * Event Store — SQLite persistence layer for tool events.
 *
 * Stores tool usage events for pattern detection. Uses a hybrid scope model:
 * - Global storage: All events in a single SQLite database
 * - Project tagging: Each event tagged with project_path for filtering
 *
 * Ported from Python core/event_store.py.
 * Key changes:
 * - Uses openDatabase() from ./db instead of sqlite3.connect()
 * - Uses ulid() from ../util/ulid instead of uuid4()
 * - Synchronous API (better-sqlite3 is sync)
 */

import { openDatabase, type Database } from "./db";
import { ulid } from "../util/ulid";
import { getDefaultDbPath } from "../util/fs";
import type { ToolEvent, EventStoreStats } from "../types";

const MAX_RESPONSE_LENGTH = 1000;

/**
 * Truncate large responses to save storage space.
 */
function truncateResponse(
  response: string | null | undefined,
  maxLength: number = MAX_RESPONSE_LENGTH,
): string | null {
  if (response == null) return null;
  if (response.length <= maxLength) return response;
  return response.slice(0, maxLength) + "...[truncated]";
}

/**
 * Convert a database row (plain object) to a ToolEvent.
 */
function rowToEvent(row: Record<string, unknown>): ToolEvent {
  return {
    id: row.id as string,
    sessionId: row.session_id as string,
    projectPath: row.project_path as string,
    toolName: row.tool_name as string,
    toolInput: JSON.parse(row.tool_input as string) as Record<string, unknown>,
    toolResponse: (row.tool_response as string) ?? null,
    success: Boolean(row.success),
    timestamp: row.timestamp as string,
    agentId: (row.agent_id as string) ?? undefined,
  };
}

/**
 * SQLite-backed event storage for tool usage patterns.
 */
export class EventStore {
  private db: Database;

  /**
   * Create an EventStore.
   *
   * @param dbPath - Path to SQLite database. Defaults to ~/.claude/auto-skill/index.db
   */
  constructor(dbPath?: string) {
    this.db = openDatabase(dbPath ?? getDefaultDbPath());
    this.initSchema();
  }

  /**
   * Create database schema if it doesn't exist.
   */
  private initSchema(): void {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS events (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        project_path TEXT NOT NULL,
        tool_name TEXT NOT NULL,
        tool_input TEXT NOT NULL,
        tool_response TEXT,
        success INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        agent_id TEXT
      )
    `);
    this.db.exec(
      "CREATE INDEX IF NOT EXISTS idx_session_id ON events(session_id)",
    );
    this.db.exec(
      "CREATE INDEX IF NOT EXISTS idx_project_path ON events(project_path)",
    );
    this.db.exec(
      "CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)",
    );
    this.db.exec(
      "CREATE INDEX IF NOT EXISTS idx_tool_name ON events(tool_name)",
    );
  }

  /**
   * Record a tool usage event.
   *
   * @returns The recorded ToolEvent.
   */
  recordEvent(
    sessionId: string,
    projectPath: string,
    toolName: string,
    toolInput: Record<string, unknown>,
    toolResponse?: string | null,
    success: boolean = true,
    agentId?: string,
  ): ToolEvent {
    const id = ulid();
    const timestamp = new Date().toISOString();

    const event: ToolEvent = {
      id,
      sessionId,
      projectPath,
      toolName,
      toolInput,
      toolResponse: truncateResponse(toolResponse) ?? null,
      success,
      timestamp,
      agentId,
    };

    this.db
      .prepare(
        `INSERT INTO events (id, session_id, project_path, tool_name,
                             tool_input, tool_response, success, timestamp, agent_id)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      )
      .run(
        event.id,
        event.sessionId,
        event.projectPath,
        event.toolName,
        JSON.stringify(event.toolInput),
        event.toolResponse,
        event.success ? 1 : 0,
        event.timestamp,
        event.agentId ?? null,
      );

    return event;
  }

  /**
   * Get all events for a specific session, ordered by timestamp.
   */
  getSessionEvents(sessionId: string): ToolEvent[] {
    const rows = this.db
      .prepare(
        `SELECT * FROM events
         WHERE session_id = ?
         ORDER BY timestamp ASC`,
      )
      .all(sessionId) as Record<string, unknown>[];

    return rows.map(rowToEvent);
  }

  /**
   * Get tool sequences from sessions, grouped by session.
   *
   * @param projectPath - Filter to specific project (undefined for all).
   * @param lookbackDays - How many days back to look (default 7).
   * @param minSequenceLength - Minimum number of tools in a sequence (default 2).
   * @returns List of tool name sequences (one per session).
   */
  getToolSequences(
    projectPath?: string,
    lookbackDays: number = 7,
    minSequenceLength: number = 2,
  ): string[][] {
    const cutoff = new Date(
      Date.now() - lookbackDays * 24 * 60 * 60 * 1000,
    ).toISOString();

    let sql = `
      SELECT session_id, tool_name
      FROM events
      WHERE timestamp > ?
    `;
    const params: unknown[] = [cutoff];

    if (projectPath) {
      sql += " AND project_path = ?";
      params.push(projectPath);
    }

    sql += " ORDER BY session_id, timestamp ASC";

    const rows = this.db.prepare(sql).all(...params) as Array<{
      session_id: string;
      tool_name: string;
    }>;

    const sequences: string[][] = [];
    let currentSession: string | null = null;
    let currentSequence: string[] = [];

    for (const row of rows) {
      if (row.session_id !== currentSession) {
        if (currentSequence.length >= minSequenceLength) {
          sequences.push(currentSequence);
        }
        currentSession = row.session_id;
        currentSequence = [];
      }
      currentSequence.push(row.tool_name);
    }

    // Don't forget the last session
    if (currentSequence.length >= minSequenceLength) {
      sequences.push(currentSequence);
    }

    return sequences;
  }

  /**
   * Get full events (including inputs) grouped by session.
   *
   * Useful for more sophisticated pattern matching that considers inputs.
   */
  getEventsWithInputs(
    projectPath?: string,
    lookbackDays: number = 7,
  ): ToolEvent[][] {
    const cutoff = new Date(
      Date.now() - lookbackDays * 24 * 60 * 60 * 1000,
    ).toISOString();

    let sql = `
      SELECT * FROM events
      WHERE timestamp > ?
    `;
    const params: unknown[] = [cutoff];

    if (projectPath) {
      sql += " AND project_path = ?";
      params.push(projectPath);
    }

    sql += " ORDER BY session_id, timestamp ASC";

    const rows = this.db.prepare(sql).all(...params) as Record<
      string,
      unknown
    >[];

    const sessions: ToolEvent[][] = [];
    let currentSession: string | null = null;
    let currentEvents: ToolEvent[] = [];

    for (const row of rows) {
      const event = rowToEvent(row);
      if (event.sessionId !== currentSession) {
        if (currentEvents.length > 0) {
          sessions.push(currentEvents);
        }
        currentSession = event.sessionId;
        currentEvents = [];
      }
      currentEvents.push(event);
    }

    if (currentEvents.length > 0) {
      sessions.push(currentEvents);
    }

    return sessions;
  }

  /**
   * Get basic statistics about stored events.
   */
  getStats(): EventStoreStats {
    const totalEvents = (
      this.db.prepare("SELECT COUNT(*) AS cnt FROM events").get() as {
        cnt: number;
      }
    ).cnt;

    const uniqueSessions = (
      this.db
        .prepare("SELECT COUNT(DISTINCT session_id) AS cnt FROM events")
        .get() as { cnt: number }
    ).cnt;

    const uniqueProjects = (
      this.db
        .prepare("SELECT COUNT(DISTINCT project_path) AS cnt FROM events")
        .get() as { cnt: number }
    ).cnt;

    const toolRows = this.db
      .prepare(
        `SELECT tool_name, COUNT(*) AS count
         FROM events
         GROUP BY tool_name
         ORDER BY count DESC
         LIMIT 10`,
      )
      .all() as Array<{ tool_name: string; count: number }>;

    return {
      totalEvents,
      uniqueSessions,
      uniqueProjects,
      topTools: toolRows.map((r) => ({ tool: r.tool_name, count: r.count })),
    };
  }

  /**
   * Delete events older than specified days.
   *
   * @param days - Number of days to keep (default 30).
   * @returns Count of deleted events.
   */
  cleanupOldEvents(days: number = 30): number {
    const cutoff = new Date(
      Date.now() - days * 24 * 60 * 60 * 1000,
    ).toISOString();

    const result = this.db
      .prepare("DELETE FROM events WHERE timestamp < ?")
      .run(cutoff);

    return result.changes;
  }

  /**
   * Close the database connection.
   */
  close(): void {
    this.db.close();
  }
}

/**
 * Factory function to create an EventStore instance.
 */
export function createEventStore(dbPath?: string): EventStore {
  return new EventStore(dbPath);
}
