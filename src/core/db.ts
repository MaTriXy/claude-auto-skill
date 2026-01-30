/**
 * Database factory — opens SQLite with WAL mode, foreign keys, optional sqlite-vec.
 * Supports both Node (better-sqlite3) and Bun (bun:sqlite).
 */
import path from "node:path";
import fs from "node:fs";

// Storage layout version for future-proofing (from babysitter pattern)
export const STORAGE_LAYOUT_VERSION = "2026.01-v4";

export interface Database {
  prepare(sql: string): Statement;
  exec(sql: string): void;
  pragma(pragma: string): unknown;
  close(): void;
  transaction<T>(fn: () => T): () => T;
}

export interface Statement {
  run(...params: unknown[]): RunResult;
  get(...params: unknown[]): unknown;
  all(...params: unknown[]): unknown[];
}

export interface RunResult {
  changes: number;
  lastInsertRowid: number | bigint;
}

let sqliteVecAvailable = false;

export function openDatabase(dbPath: string): Database {
  // Ensure parent directory exists
  const dir = path.dirname(dbPath);
  fs.mkdirSync(dir, { recursive: true, mode: 0o700 });

  let db: Database;

  // @ts-ignore — Bun global detection
  if (typeof Bun !== "undefined") {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { Database: BunDB } = require("bun:sqlite");
    db = new BunDB(dbPath) as unknown as Database;
  } else {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const BetterSqlite3 = require("better-sqlite3");
    db = new BetterSqlite3(dbPath) as Database;
  }

  // qmd-style connection setup
  db.pragma("journal_mode = WAL");
  db.pragma("foreign_keys = ON");

  // Optional: load sqlite-vec for vector search
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const vec = require("sqlite-vec");
    (db as any).loadExtension(vec.getLoadablePath());
    sqliteVecAvailable = true;
  } catch {
    // sqlite-vec not installed — FTS5 still works
  }

  return db;
}

export function isSqliteVecAvailable(): boolean {
  return sqliteVecAvailable;
}
