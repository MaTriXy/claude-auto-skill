/**
 * Database Migration System — Schema versioning and upgrade management.
 *
 * Provides automatic schema upgrades for the EventStore, Telemetry,
 * SkillTracker, and SkillStore (FTS5) databases.
 *
 * Ported from Python core/migrations.py.
 * Key changes:
 * - Uses Database interface from ./db instead of sqlite3
 * - TypeScript types for Migration, MigrationManager
 * - Includes all existing migrations (event store 1-4, telemetry 1, skill tracker 1)
 * - NEW migration for FTS5 skill store schema (tables + triggers + indexes)
 */

import { openDatabase, type Database } from "./db";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Migration {
  version: number;
  name: string;
  description: string;
  up: (db: Database) => void;
  down?: (db: Database) => void;
}

export class MigrationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "MigrationError";
  }
}

// ---------------------------------------------------------------------------
// MigrationManager
// ---------------------------------------------------------------------------

/**
 * Manages database schema migrations.
 *
 * Tracks schema version and applies migrations in order.
 */
export class MigrationManager {
  private db: Database;
  private migrations: Migration[] = [];

  constructor(dbPath: string) {
    this.db = openDatabase(dbPath);
    this.ensureMigrationTable();
  }

  private ensureMigrationTable(): void {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        applied_at TEXT NOT NULL
      )
    `);
  }

  /**
   * Register a migration.
   */
  register(migration: Migration): void {
    this.migrations.push(migration);
    this.migrations.sort((a, b) => a.version - b.version);
  }

  /**
   * Get current schema version.
   *
   * @returns Current version number, or 0 if no migrations applied.
   */
  getCurrentVersion(): number {
    const row = this.db
      .prepare("SELECT MAX(version) AS ver FROM schema_migrations")
      .get() as { ver: number | null } | undefined;
    return row?.ver ?? 0;
  }

  /**
   * Get list of migrations that haven't been applied.
   */
  getPendingMigrations(): Migration[] {
    const current = this.getCurrentVersion();
    return this.migrations.filter((m) => m.version > current);
  }

  /**
   * Apply a single migration.
   */
  applyMigration(migration: Migration): void {
    try {
      const run = this.db.transaction(() => {
        migration.up(this.db);
        this.db
          .prepare(
            `INSERT INTO schema_migrations (version, name, applied_at)
             VALUES (?, ?, ?)`,
          )
          .run(migration.version, migration.name, new Date().toISOString());
      });
      run();
    } catch (err) {
      throw new MigrationError(
        `Failed to apply migration ${migration.version} (${migration.name}): ${err}`,
      );
    }
  }

  /**
   * Apply all pending migrations up to target version.
   *
   * @param targetVersion - Version to migrate to (default: latest).
   */
  migrate(targetVersion?: number): void {
    let pending = this.getPendingMigrations();

    if (targetVersion !== undefined) {
      pending = pending.filter((m) => m.version <= targetVersion);
    }

    if (pending.length === 0) {
      return;
    }

    for (const migration of pending) {
      this.applyMigration(migration);
    }
  }

  /**
   * Rollback to a specific version.
   *
   * @param targetVersion - Version to rollback to.
   */
  rollback(targetVersion: number): void {
    const current = this.getCurrentVersion();
    if (targetVersion >= current) {
      return;
    }

    // Get migrations to rollback (in reverse order)
    const toRollback = [...this.migrations]
      .reverse()
      .filter(
        (m) => m.version > targetVersion && m.version <= current,
      );

    for (const migration of toRollback) {
      if (!migration.down) {
        throw new MigrationError(
          `Migration ${migration.version} (${migration.name}) does not support rollback`,
        );
      }

      try {
        const run = this.db.transaction(() => {
          migration.down!(this.db);
          this.db
            .prepare("DELETE FROM schema_migrations WHERE version = ?")
            .run(migration.version);
        });
        run();
      } catch (err) {
        throw new MigrationError(
          `Failed to rollback migration ${migration.version} (${migration.name}): ${err}`,
        );
      }
    }
  }

  /**
   * Get migration status info.
   */
  status(): {
    dbPath: string;
    currentVersion: number;
    totalMigrations: number;
    pendingMigrations: number;
    migrations: Array<{
      version: number;
      name: string;
      applied: boolean;
    }>;
  } {
    const current = this.getCurrentVersion();
    const pending = this.getPendingMigrations();

    return {
      dbPath: "(managed)",
      currentVersion: current,
      totalMigrations: this.migrations.length,
      pendingMigrations: pending.length,
      migrations: this.migrations.map((m) => ({
        version: m.version,
        name: m.name,
        applied: m.version <= current,
      })),
    };
  }

  /**
   * Close the database connection.
   */
  close(): void {
    this.db.close();
  }
}

// ---------------------------------------------------------------------------
// Pre-defined migration sets
// ---------------------------------------------------------------------------

/**
 * Create a MigrationManager pre-loaded with EventStore migrations.
 */
export function createEventStoreMigrations(dbPath: string): MigrationManager {
  const manager = new MigrationManager(dbPath);

  // Migration 1: Initial schema (baseline)
  manager.register({
    version: 1,
    name: "initial_schema",
    description: "Create tool_events table with indexes",
    up(db: Database) {
      db.exec(`
        CREATE TABLE IF NOT EXISTS tool_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          session_id TEXT NOT NULL,
          tool_name TEXT NOT NULL,
          timestamp TEXT NOT NULL,
          success INTEGER NOT NULL,
          metadata TEXT,
          project_path TEXT,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
      `);
      db.exec(
        "CREATE INDEX IF NOT EXISTS idx_session_id ON tool_events(session_id)",
      );
      db.exec(
        "CREATE INDEX IF NOT EXISTS idx_timestamp ON tool_events(timestamp)",
      );
    },
  });

  // Migration 2: Add tool_events.inputs column
  manager.register({
    version: 2,
    name: "add_inputs_column",
    description: "Add inputs column to track tool inputs",
    up(db: Database) {
      db.exec("ALTER TABLE tool_events ADD COLUMN inputs TEXT");
    },
    down(db: Database) {
      // SQLite doesn't support DROP COLUMN in older versions, recreate table
      db.exec(`
        CREATE TABLE tool_events_backup AS
        SELECT id, session_id, tool_name, timestamp, success, metadata,
               project_path, created_at
        FROM tool_events
      `);
      db.exec("DROP TABLE tool_events");
      db.exec("ALTER TABLE tool_events_backup RENAME TO tool_events");
      db.exec(
        "CREATE INDEX idx_session_id ON tool_events(session_id)",
      );
      db.exec(
        "CREATE INDEX idx_timestamp ON tool_events(timestamp)",
      );
    },
  });

  // Migration 3: Add project_path index
  manager.register({
    version: 3,
    name: "add_project_index",
    description: "Add index on project_path for performance",
    up(db: Database) {
      db.exec(
        "CREATE INDEX IF NOT EXISTS idx_project_path ON tool_events(project_path)",
      );
    },
    down(db: Database) {
      db.exec("DROP INDEX IF EXISTS idx_project_path");
    },
  });

  // Migration 4: Add agent_id column
  manager.register({
    version: 4,
    name: "add_agent_id",
    description: "Add agent_id column for multi-agent tracking",
    up(db: Database) {
      db.exec("ALTER TABLE tool_events ADD COLUMN agent_id TEXT");
      db.exec(
        "CREATE INDEX IF NOT EXISTS idx_agent_id ON tool_events(agent_id)",
      );
    },
    down(db: Database) {
      db.exec(`
        CREATE TABLE tool_events_backup AS
        SELECT id, session_id, tool_name, timestamp, success, metadata,
               project_path, created_at, inputs
        FROM tool_events
      `);
      db.exec("DROP TABLE tool_events");
      db.exec("ALTER TABLE tool_events_backup RENAME TO tool_events");
      db.exec(
        "CREATE INDEX idx_session_id ON tool_events(session_id)",
      );
      db.exec(
        "CREATE INDEX idx_timestamp ON tool_events(timestamp)",
      );
      db.exec(
        "CREATE INDEX idx_project_path ON tool_events(project_path)",
      );
    },
  });

  return manager;
}

/**
 * Create a MigrationManager pre-loaded with Telemetry migrations.
 */
export function createTelemetryMigrations(dbPath: string): MigrationManager {
  const manager = new MigrationManager(dbPath);

  // Migration 1: Initial schema
  manager.register({
    version: 1,
    name: "initial_telemetry",
    description: "Create skill_telemetry table with indexes",
    up(db: Database) {
      db.exec(`
        CREATE TABLE IF NOT EXISTS skill_telemetry (
          id TEXT PRIMARY KEY,
          skill_id TEXT NOT NULL,
          skill_name TEXT NOT NULL,
          session_id TEXT NOT NULL,
          agent_id TEXT NOT NULL DEFAULT 'unknown',
          duration_ms INTEGER,
          outcome TEXT NOT NULL,
          timestamp TEXT NOT NULL
        )
      `);
      db.exec(
        "CREATE INDEX IF NOT EXISTS idx_telemetry_skill ON skill_telemetry(skill_id)",
      );
      db.exec(
        "CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON skill_telemetry(timestamp)",
      );
    },
  });

  return manager;
}

/**
 * Create a MigrationManager pre-loaded with SkillTracker migrations.
 */
export function createSkillTrackerMigrations(
  dbPath: string,
): MigrationManager {
  const manager = new MigrationManager(dbPath);

  // Migration 1: Initial schema
  manager.register({
    version: 1,
    name: "initial_schema",
    description: "Create skill_adoptions table with indexes",
    up(db: Database) {
      db.exec(`
        CREATE TABLE IF NOT EXISTS skill_adoptions (
          skill_id TEXT PRIMARY KEY,
          skill_name TEXT NOT NULL,
          source TEXT NOT NULL,
          initial_confidence REAL NOT NULL,
          current_confidence REAL NOT NULL,
          usage_count INTEGER DEFAULT 0,
          success_count INTEGER DEFAULT 0,
          failure_count INTEGER DEFAULT 0,
          first_used TEXT NOT NULL,
          last_used TEXT NOT NULL,
          graduated_to_local INTEGER DEFAULT 0,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
      `);
      db.exec(
        "CREATE INDEX IF NOT EXISTS idx_confidence ON skill_adoptions(current_confidence)",
      );
      db.exec(
        "CREATE INDEX IF NOT EXISTS idx_source ON skill_adoptions(source)",
      );
    },
  });

  return manager;
}

/**
 * Create a MigrationManager pre-loaded with FTS5 SkillStore migrations.
 *
 * This is the NEW migration set for the content-addressable skill store
 * with FTS5 full-text search and auto-sync triggers.
 */
export function createSkillStoreMigrations(dbPath: string): MigrationManager {
  const manager = new MigrationManager(dbPath);

  // Migration 1: Content-addressable storage + FTS5
  manager.register({
    version: 1,
    name: "fts5_skill_store",
    description:
      "Create content-addressable skill store with FTS5 search and auto-sync triggers",
    up(db: Database) {
      // Content-addressable storage
      db.exec(`
        CREATE TABLE IF NOT EXISTS skill_content (
          hash TEXT PRIMARY KEY,
          body TEXT NOT NULL,
          frontmatter TEXT,
          created_at TEXT DEFAULT (datetime('now'))
        )
      `);

      // Skill metadata table
      db.exec(`
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
        )
      `);

      // Indexes
      db.exec(
        "CREATE INDEX IF NOT EXISTS idx_skills_collection ON skills(collection)",
      );
      db.exec(
        "CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(name)",
      );
      db.exec(
        "CREATE INDEX IF NOT EXISTS idx_skills_hash ON skills(hash)",
      );
      db.exec(
        "CREATE INDEX IF NOT EXISTS idx_skills_active ON skills(active)",
      );

      // FTS5 virtual table
      db.exec(`
        CREATE VIRTUAL TABLE IF NOT EXISTS skills_fts USING fts5(
          name,
          description,
          body,
          tags,
          content='skills',
          content_rowid='rowid',
          tokenize='unicode61'
        )
      `);

      // Auto-sync triggers
      db.exec(`
        CREATE TRIGGER IF NOT EXISTS skills_ai AFTER INSERT ON skills BEGIN
          INSERT INTO skills_fts(rowid, name, description, body, tags)
          SELECT new.rowid, new.name, new.description, sc.body, new.tags
          FROM skill_content sc WHERE sc.hash = new.hash;
        END
      `);

      db.exec(`
        CREATE TRIGGER IF NOT EXISTS skills_ad AFTER DELETE ON skills BEGIN
          INSERT INTO skills_fts(skills_fts, rowid, name, description, body, tags)
          VALUES('delete', old.rowid, old.name, old.description,
            (SELECT body FROM skill_content WHERE hash = old.hash), old.tags);
        END
      `);

      db.exec(`
        CREATE TRIGGER IF NOT EXISTS skills_au AFTER UPDATE ON skills BEGIN
          INSERT INTO skills_fts(skills_fts, rowid, name, description, body, tags)
          VALUES('delete', old.rowid, old.name, old.description,
            (SELECT body FROM skill_content WHERE hash = old.hash), old.tags);
          INSERT INTO skills_fts(rowid, name, description, body, tags)
          SELECT new.rowid, new.name, new.description, sc.body, new.tags
          FROM skill_content sc WHERE sc.hash = new.hash;
        END
      `);
    },
    down(db: Database) {
      db.exec("DROP TRIGGER IF EXISTS skills_au");
      db.exec("DROP TRIGGER IF EXISTS skills_ad");
      db.exec("DROP TRIGGER IF EXISTS skills_ai");
      db.exec("DROP TABLE IF EXISTS skills_fts");
      db.exec("DROP TABLE IF EXISTS skills");
      db.exec("DROP TABLE IF EXISTS skill_content");
    },
  });

  return manager;
}
