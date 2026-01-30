/**
 * Skill Store — Content-addressable skill storage with FTS5 full-text search.
 *
 * Adopted from qmd's store.ts pattern. Three tables:
 * - skill_content: SHA-256 keyed bodies (content-addressable)
 * - skills: metadata + collection + FK to content
 * - skills_fts: FTS5 virtual table with auto-sync triggers
 *
 * Factory function `createSkillStore(dbPath?)` returns a SkillStore interface.
 */

import { createHash } from "node:crypto";
import { openDatabase, type Database } from "./db";
import { ulid } from "../util/ulid";
import { getDefaultDbPath } from "../util/fs";
import { sanitizeFTSQuery } from "../util/fts";
import type {
  SkillContent,
  SkillRecord,
  CollectionInfo,
  SearchOptions,
  SearchResult,
} from "../types";

// ---------------------------------------------------------------------------
// Schema
// ---------------------------------------------------------------------------

const SCHEMA_SQL = `
  -- Content-addressable skill storage
  CREATE TABLE IF NOT EXISTS skill_content (
    hash TEXT PRIMARY KEY,
    body TEXT NOT NULL,
    frontmatter TEXT,
    created_at TEXT DEFAULT (datetime('now'))
  );

  -- Skill metadata referencing content by hash
  CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    collection TEXT NOT NULL DEFAULT 'auto',
    filepath TEXT,
    hash TEXT REFERENCES skill_content(hash),
    description TEXT,
    tags TEXT,
    confidence REAL DEFAULT 0.5,
    agent_type TEXT,
    active INTEGER DEFAULT 1,
    source_url TEXT,
    author TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
  );

  CREATE INDEX IF NOT EXISTS idx_skills_collection ON skills(collection);
  CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(name);
  CREATE INDEX IF NOT EXISTS idx_skills_hash ON skills(hash);
  CREATE INDEX IF NOT EXISTS idx_skills_active ON skills(active);
`;

const FTS_SQL = `
  -- FTS5 full-text index (unicode61 tokenizer for proper Unicode handling)
  CREATE VIRTUAL TABLE IF NOT EXISTS skills_fts USING fts5(
    name,
    description,
    body,
    tags,
    content='skills',
    content_rowid='rowid',
    tokenize='unicode61'
  );
`;

const TRIGGERS_SQL = `
  -- Auto-sync trigger: INSERT on skills → INSERT into skills_fts
  CREATE TRIGGER IF NOT EXISTS skills_ai AFTER INSERT ON skills BEGIN
    INSERT INTO skills_fts(rowid, name, description, body, tags)
    SELECT new.rowid, new.name, new.description, sc.body, new.tags
    FROM skill_content sc WHERE sc.hash = new.hash;
  END;

  -- Auto-sync trigger: DELETE on skills → DELETE from skills_fts
  CREATE TRIGGER IF NOT EXISTS skills_ad AFTER DELETE ON skills BEGIN
    INSERT INTO skills_fts(skills_fts, rowid, name, description, body, tags)
    VALUES('delete', old.rowid, old.name, old.description,
      (SELECT body FROM skill_content WHERE hash = old.hash), old.tags);
  END;

  -- Auto-sync trigger: UPDATE on skills → re-sync skills_fts
  CREATE TRIGGER IF NOT EXISTS skills_au AFTER UPDATE ON skills BEGIN
    INSERT INTO skills_fts(skills_fts, rowid, name, description, body, tags)
    VALUES('delete', old.rowid, old.name, old.description,
      (SELECT body FROM skill_content WHERE hash = old.hash), old.tags);
    INSERT INTO skills_fts(rowid, name, description, body, tags)
    SELECT new.rowid, new.name, new.description, sc.body, new.tags
    FROM skill_content sc WHERE sc.hash = new.hash;
  END;
`;

// ---------------------------------------------------------------------------
// Types for the store (input types, distinct from DB row types)
// ---------------------------------------------------------------------------

/** Input for inserting a new skill. */
export interface NewSkill {
  name: string;
  collection?: string;
  filepath?: string;
  hash: string;
  description?: string;
  tags?: string[];
  confidence?: number;
  agentType?: string;
  sourceUrl?: string;
  author?: string;
}

/** The full SkillStore interface. */
export interface SkillStore {
  // Content-addressable storage
  insertContent(body: string, frontmatter?: Record<string, unknown>): string;
  getContent(hash: string): SkillContent | undefined;

  // Skill CRUD
  insertSkill(skill: NewSkill): string;
  updateSkill(id: string, updates: Partial<NewSkill>): void;
  deactivateSkill(id: string): void;
  getSkill(nameOrId: string): (SkillRecord & { body?: string }) | undefined;
  getSkillByHash(hash: string): SkillRecord | undefined;
  listSkills(collection?: string): SkillRecord[];

  // FTS5 search
  searchSkills(query: string, opts?: SearchOptions): SearchResult[];

  // Collection management
  getCollectionStats(): CollectionInfo[];

  // Maintenance
  vacuumDatabase(): void;
  cleanupOrphanedContent(): number;

  // Close
  close(): void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Compute SHA-256 hex digest of content.
 */
function hashContent(body: string): string {
  return createHash("sha256").update(body, "utf8").digest("hex");
}

/**
 * Convert a raw DB row into a SkillRecord.
 */
function rowToSkillRecord(row: Record<string, unknown>): SkillRecord {
  return {
    id: row.id as string,
    name: row.name as string,
    collection: row.collection as string,
    filepath: (row.filepath as string) ?? "",
    hash: row.hash as string,
    description: (row.description as string) ?? "",
    tags: row.tags ? (JSON.parse(row.tags as string) as string[]) : [],
    confidence: (row.confidence as number) ?? 0.5,
    agentType: (row.agent_type as string) ?? null,
    active: Boolean(row.active),
    sourceUrl: (row.source_url as string) ?? "",
    author: (row.author as string) ?? "",
    createdAt: row.created_at as string,
    updatedAt: row.updated_at as string,
  };
}

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

/**
 * Create a content-addressable skill store backed by SQLite with FTS5 search.
 *
 * @param dbPath - Path to the SQLite database. Defaults to ~/.claude/auto-skill/index.db
 */
export function createSkillStore(dbPath?: string): SkillStore {
  const db = openDatabase(dbPath ?? getDefaultDbPath());
  initializeSchema(db);

  return {
    insertContent(body: string, frontmatter?: Record<string, unknown>): string {
      const hash = hashContent(body);
      db.prepare(
        `INSERT OR IGNORE INTO skill_content (hash, body, frontmatter)
         VALUES (?, ?, ?)`,
      ).run(hash, body, frontmatter ? JSON.stringify(frontmatter) : null);
      return hash;
    },

    getContent(hash: string): SkillContent | undefined {
      const row = db
        .prepare("SELECT * FROM skill_content WHERE hash = ?")
        .get(hash) as Record<string, unknown> | undefined;
      if (!row) return undefined;
      return {
        hash: row.hash as string,
        body: row.body as string,
        frontmatter: row.frontmatter
          ? (JSON.parse(row.frontmatter as string) as Record<string, unknown>)
          : {},
        createdAt: row.created_at as string,
      };
    },

    insertSkill(skill: NewSkill): string {
      const id = ulid();
      const now = new Date().toISOString();
      db.prepare(
        `INSERT INTO skills
           (id, name, collection, filepath, hash, description, tags,
            confidence, agent_type, active, source_url, author,
            created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)`,
      ).run(
        id,
        skill.name,
        skill.collection ?? "auto",
        skill.filepath ?? null,
        skill.hash,
        skill.description ?? null,
        skill.tags ? JSON.stringify(skill.tags) : null,
        skill.confidence ?? 0.5,
        skill.agentType ?? null,
        skill.sourceUrl ?? null,
        skill.author ?? null,
        now,
        now,
      );
      return id;
    },

    updateSkill(id: string, updates: Partial<NewSkill>): void {
      const setClauses: string[] = [];
      const params: unknown[] = [];

      if (updates.name !== undefined) {
        setClauses.push("name = ?");
        params.push(updates.name);
      }
      if (updates.collection !== undefined) {
        setClauses.push("collection = ?");
        params.push(updates.collection);
      }
      if (updates.filepath !== undefined) {
        setClauses.push("filepath = ?");
        params.push(updates.filepath);
      }
      if (updates.hash !== undefined) {
        setClauses.push("hash = ?");
        params.push(updates.hash);
      }
      if (updates.description !== undefined) {
        setClauses.push("description = ?");
        params.push(updates.description);
      }
      if (updates.tags !== undefined) {
        setClauses.push("tags = ?");
        params.push(JSON.stringify(updates.tags));
      }
      if (updates.confidence !== undefined) {
        setClauses.push("confidence = ?");
        params.push(updates.confidence);
      }
      if (updates.agentType !== undefined) {
        setClauses.push("agent_type = ?");
        params.push(updates.agentType);
      }
      if (updates.sourceUrl !== undefined) {
        setClauses.push("source_url = ?");
        params.push(updates.sourceUrl);
      }
      if (updates.author !== undefined) {
        setClauses.push("author = ?");
        params.push(updates.author);
      }

      if (setClauses.length === 0) return;

      setClauses.push("updated_at = ?");
      params.push(new Date().toISOString());
      params.push(id);

      db.prepare(
        `UPDATE skills SET ${setClauses.join(", ")} WHERE id = ?`,
      ).run(...params);
    },

    deactivateSkill(id: string): void {
      db.prepare(
        "UPDATE skills SET active = 0, updated_at = ? WHERE id = ?",
      ).run(new Date().toISOString(), id);
    },

    getSkill(
      nameOrId: string,
    ): (SkillRecord & { body?: string }) | undefined {
      // Try by id first
      let row = db
        .prepare(
          `SELECT s.*, sc.body AS body
           FROM skills s
           LEFT JOIN skill_content sc ON sc.hash = s.hash
           WHERE s.id = ?`,
        )
        .get(nameOrId) as Record<string, unknown> | undefined;

      // Fall back to name
      if (!row) {
        row = db
          .prepare(
            `SELECT s.*, sc.body AS body
             FROM skills s
             LEFT JOIN skill_content sc ON sc.hash = s.hash
             WHERE s.name = ?`,
          )
          .get(nameOrId) as Record<string, unknown> | undefined;
      }

      if (!row) return undefined;

      const record = rowToSkillRecord(row);
      return { ...record, body: (row.body as string) ?? undefined };
    },

    getSkillByHash(hash: string): SkillRecord | undefined {
      const row = db
        .prepare("SELECT * FROM skills WHERE hash = ? LIMIT 1")
        .get(hash) as Record<string, unknown> | undefined;
      if (!row) return undefined;
      return rowToSkillRecord(row);
    },

    listSkills(collection?: string): SkillRecord[] {
      let sql = "SELECT * FROM skills WHERE active = 1";
      const params: unknown[] = [];
      if (collection) {
        sql += " AND collection = ?";
        params.push(collection);
      }
      sql += " ORDER BY updated_at DESC";

      const rows = db.prepare(sql).all(...params) as Record<
        string,
        unknown
      >[];
      return rows.map(rowToSkillRecord);
    },

    searchSkills(query: string, opts: SearchOptions = {}): SearchResult[] {
      const {
        collection,
        limit = 10,
        minScore,
        activeOnly = true,
      } = opts;

      const sanitized = sanitizeFTSQuery(query);
      if (!sanitized) return [];

      let sql = `
        SELECT s.*, sc.body, sc.frontmatter, bm25(skills_fts) AS score
        FROM skills_fts fts
        JOIN skills s ON s.rowid = fts.rowid
        JOIN skill_content sc ON sc.hash = s.hash
        WHERE skills_fts MATCH ?
      `;
      const params: unknown[] = [sanitized];

      if (activeOnly) {
        sql += " AND s.active = 1";
      }
      if (collection) {
        sql += " AND s.collection = ?";
        params.push(collection);
      }
      if (minScore !== undefined) {
        // BM25 scores are negative; lower (more negative) = better match
        sql += " AND bm25(skills_fts) <= ?";
        params.push(minScore);
      }

      sql += " ORDER BY bm25(skills_fts) LIMIT ?";
      params.push(limit);

      const rows = db.prepare(sql).all(...params) as Record<
        string,
        unknown
      >[];

      return rows.map((row) => ({
        ...rowToSkillRecord(row),
        body: (row.body as string) ?? undefined,
        score: row.score as number,
      }));
    },

    getCollectionStats(): CollectionInfo[] {
      const rows = db
        .prepare(
          `SELECT
             collection AS name,
             COUNT(*) AS count,
             AVG(confidence) AS avgConfidence
           FROM skills
           WHERE active = 1
           GROUP BY collection
           ORDER BY collection`,
        )
        .all() as Array<{
        name: string;
        count: number;
        avgConfidence: number;
      }>;
      return rows;
    },

    vacuumDatabase(): void {
      db.exec("VACUUM");
    },

    cleanupOrphanedContent(): number {
      const result = db
        .prepare(
          `DELETE FROM skill_content
           WHERE hash NOT IN (SELECT DISTINCT hash FROM skills WHERE hash IS NOT NULL)`,
        )
        .run();
      return result.changes;
    },

    close(): void {
      db.close();
    },
  };
}

// ---------------------------------------------------------------------------
// Schema initialization (internal)
// ---------------------------------------------------------------------------

function initializeSchema(db: Database): void {
  db.exec(SCHEMA_SQL);
  db.exec(FTS_SQL);
  db.exec(TRIGGERS_SQL);
}
