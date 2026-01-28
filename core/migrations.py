"""
Database Migration System - Schema versioning and upgrade management.

Provides automatic schema upgrades for the EventStore and SkillTracker databases.
"""

import sqlite3
from pathlib import Path
from typing import List, Callable, Optional
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Migration:
    """A database migration."""
    
    version: int
    name: str
    description: str
    up: Callable[[sqlite3.Connection], None]
    down: Optional[Callable[[sqlite3.Connection], None]] = None


class MigrationError(Exception):
    """Raised when a migration fails."""
    pass


class MigrationManager:
    """
    Manages database schema migrations.
    
    Tracks schema version and applies migrations in order.
    """
    
    def __init__(self, db_path: Path):
        """
        Initialize migration manager.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.migrations: List[Migration] = []
        self._ensure_migration_table()
    
    def _ensure_migration_table(self):
        """Create migrations table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                )
            """)
            conn.commit()
    
    def register(
        self,
        version: int,
        name: str,
        description: str,
        up: Callable[[sqlite3.Connection], None],
        down: Optional[Callable[[sqlite3.Connection], None]] = None
    ):
        """
        Register a migration.
        
        Args:
            version: Migration version number (must be unique and sequential)
            name: Short name for the migration
            description: Detailed description
            up: Function to apply migration
            down: Optional function to rollback migration
        """
        migration = Migration(
            version=version,
            name=name,
            description=description,
            up=up,
            down=down
        )
        self.migrations.append(migration)
        # Keep migrations sorted by version
        self.migrations.sort(key=lambda m: m.version)
    
    def get_current_version(self) -> int:
        """
        Get current schema version.
        
        Returns:
            Current version number, or 0 if no migrations applied
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT MAX(version) FROM schema_migrations"
            )
            result = cursor.fetchone()[0]
            return result if result is not None else 0
    
    def get_pending_migrations(self) -> List[Migration]:
        """
        Get list of migrations that haven't been applied.
        
        Returns:
            List of pending migrations
        """
        current_version = self.get_current_version()
        return [m for m in self.migrations if m.version > current_version]
    
    def apply_migration(self, migration: Migration):
        """
        Apply a single migration.
        
        Args:
            migration: Migration to apply
            
        Raises:
            MigrationError: If migration fails
        """
        print(f"Applying migration {migration.version}: {migration.name}")
        print(f"  {migration.description}")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Apply migration
                migration.up(conn)
                
                # Record migration
                conn.execute("""
                    INSERT INTO schema_migrations (version, name, applied_at)
                    VALUES (?, ?, ?)
                """, (
                    migration.version,
                    migration.name,
                    datetime.now(timezone.utc).isoformat()
                ))
                
                conn.commit()
                print(f"  ✓ Migration {migration.version} applied successfully")
                
        except Exception as e:
            raise MigrationError(
                f"Failed to apply migration {migration.version} ({migration.name}): {e}"
            ) from e
    
    def migrate(self, target_version: Optional[int] = None):
        """
        Apply all pending migrations up to target version.
        
        Args:
            target_version: Version to migrate to (default: latest)
            
        Raises:
            MigrationError: If any migration fails
        """
        current_version = self.get_current_version()
        pending = self.get_pending_migrations()
        
        if target_version is not None:
            pending = [m for m in pending if m.version <= target_version]
        
        if not pending:
            print(f"Database is up to date (version {current_version})")
            return
        
        print(f"Current version: {current_version}")
        print(f"Target version: {target_version or 'latest'}")
        print(f"Pending migrations: {len(pending)}")
        print()
        
        for migration in pending:
            self.apply_migration(migration)
        
        final_version = self.get_current_version()
        print()
        print(f"✓ Migration complete: v{current_version} → v{final_version}")
    
    def rollback(self, target_version: int):
        """
        Rollback to a specific version.
        
        Args:
            target_version: Version to rollback to
            
        Raises:
            MigrationError: If rollback fails or migration doesn't support down()
        """
        current_version = self.get_current_version()
        
        if target_version >= current_version:
            print(f"Already at or before version {target_version}")
            return
        
        # Get migrations to rollback (in reverse order)
        to_rollback = [
            m for m in reversed(self.migrations)
            if target_version < m.version <= current_version
        ]
        
        print(f"Rolling back from v{current_version} to v{target_version}")
        print(f"Migrations to rollback: {len(to_rollback)}")
        print()
        
        for migration in to_rollback:
            if migration.down is None:
                raise MigrationError(
                    f"Migration {migration.version} ({migration.name}) "
                    "does not support rollback"
                )
            
            print(f"Rolling back migration {migration.version}: {migration.name}")
            
            try:
                with sqlite3.connect(self.db_path) as conn:
                    # Rollback migration
                    migration.down(conn)
                    
                    # Remove migration record
                    conn.execute(
                        "DELETE FROM schema_migrations WHERE version = ?",
                        (migration.version,)
                    )
                    
                    conn.commit()
                    print(f"  ✓ Migration {migration.version} rolled back")
                    
            except Exception as e:
                raise MigrationError(
                    f"Failed to rollback migration {migration.version} "
                    f"({migration.name}): {e}"
                ) from e
        
        final_version = self.get_current_version()
        print()
        print(f"✓ Rollback complete: v{current_version} → v{final_version}")
    
    def status(self):
        """Print migration status."""
        current_version = self.get_current_version()
        pending = self.get_pending_migrations()
        
        print("="*70)
        print("Database Migration Status")
        print("="*70)
        print()
        print(f"Database: {self.db_path}")
        print(f"Current version: {current_version}")
        print(f"Total migrations: {len(self.migrations)}")
        print(f"Pending migrations: {len(pending)}")
        print()
        
        if self.migrations:
            print("Available migrations:")
            print()
            for migration in self.migrations:
                status = "✓" if migration.version <= current_version else "⏳"
                print(f"  {status} v{migration.version}: {migration.name}")
                print(f"     {migration.description}")
                print()
        else:
            print("No migrations registered")


# Example migrations for EventStore

def create_event_store_migrations(db_path: Path) -> MigrationManager:
    """
    Create migration manager with EventStore migrations.
    
    Args:
        db_path: Path to EventStore database
        
    Returns:
        Configured MigrationManager
    """
    manager = MigrationManager(db_path)
    
    # Migration 1: Initial schema (baseline)
    def migration_1_up(conn: sqlite3.Connection):
        """Create initial tool_events table."""
        conn.execute("""
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
        """)
        
        # Create indexes
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_id 
            ON tool_events(session_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON tool_events(timestamp)
        """)
    
    manager.register(
        version=1,
        name="initial_schema",
        description="Create tool_events table with indexes",
        up=migration_1_up
    )
    
    # Migration 2: Add tool_events.inputs column
    def migration_2_up(conn: sqlite3.Connection):
        """Add inputs column for tool input tracking."""
        conn.execute("""
            ALTER TABLE tool_events ADD COLUMN inputs TEXT
        """)
    
    def migration_2_down(conn: sqlite3.Connection):
        """Remove inputs column (requires table recreation in SQLite)."""
        # SQLite doesn't support DROP COLUMN, need to recreate table
        conn.execute("""
            CREATE TABLE tool_events_backup AS 
            SELECT id, session_id, tool_name, timestamp, success, metadata, 
                   project_path, created_at
            FROM tool_events
        """)
        conn.execute("DROP TABLE tool_events")
        conn.execute("ALTER TABLE tool_events_backup RENAME TO tool_events")
        
        # Recreate indexes
        conn.execute("""
            CREATE INDEX idx_session_id ON tool_events(session_id)
        """)
        conn.execute("""
            CREATE INDEX idx_timestamp ON tool_events(timestamp)
        """)
    
    manager.register(
        version=2,
        name="add_inputs_column",
        description="Add inputs column to track tool inputs",
        up=migration_2_up,
        down=migration_2_down
    )
    
    # Migration 3: Add project_path index
    def migration_3_up(conn: sqlite3.Connection):
        """Add index on project_path for faster project-scoped queries."""
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_project_path 
            ON tool_events(project_path)
        """)
    
    def migration_3_down(conn: sqlite3.Connection):
        """Remove project_path index."""
        conn.execute("DROP INDEX IF EXISTS idx_project_path")
    
    manager.register(
        version=3,
        name="add_project_index",
        description="Add index on project_path for performance",
        up=migration_3_up,
        down=migration_3_down
    )

    # Migration 4: Add agent_id column
    def migration_4_up(conn: sqlite3.Connection):
        """Add agent_id column for multi-agent tracking."""
        conn.execute("""
            ALTER TABLE tool_events ADD COLUMN agent_id TEXT
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_id
            ON tool_events(agent_id)
        """)

    def migration_4_down(conn: sqlite3.Connection):
        """Remove agent_id column (requires table recreation in SQLite)."""
        conn.execute("""
            CREATE TABLE tool_events_backup AS
            SELECT id, session_id, tool_name, timestamp, success, metadata,
                   project_path, created_at, inputs
            FROM tool_events
        """)
        conn.execute("DROP TABLE tool_events")
        conn.execute("ALTER TABLE tool_events_backup RENAME TO tool_events")
        conn.execute("CREATE INDEX idx_session_id ON tool_events(session_id)")
        conn.execute("CREATE INDEX idx_timestamp ON tool_events(timestamp)")
        conn.execute("CREATE INDEX idx_project_path ON tool_events(project_path)")

    manager.register(
        version=4,
        name="add_agent_id",
        description="Add agent_id column for multi-agent tracking",
        up=migration_4_up,
        down=migration_4_down
    )

    return manager


def create_telemetry_migrations(db_path: Path) -> MigrationManager:
    """Create migration manager with Telemetry migrations.

    Args:
        db_path: Path to Telemetry database

    Returns:
        Configured MigrationManager
    """
    manager = MigrationManager(db_path)

    # Migration 1: Initial schema
    def migration_1_up(conn: sqlite3.Connection):
        """Create skill_telemetry table."""
        conn.execute("""
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
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_telemetry_skill
            ON skill_telemetry(skill_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp
            ON skill_telemetry(timestamp)
        """)

    manager.register(
        version=1,
        name="initial_telemetry",
        description="Create skill_telemetry table with indexes",
        up=migration_1_up
    )

    return manager


def create_skill_tracker_migrations(db_path: Path) -> MigrationManager:
    """
    Create migration manager with SkillTracker migrations.
    
    Args:
        db_path: Path to SkillTracker database
        
    Returns:
        Configured MigrationManager
    """
    manager = MigrationManager(db_path)
    
    # Migration 1: Initial schema
    def migration_1_up(conn: sqlite3.Connection):
        """Create skill_adoptions table."""
        conn.execute("""
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
        """)
        
        # Create indexes
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_confidence 
            ON skill_adoptions(current_confidence)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_source 
            ON skill_adoptions(source)
        """)
    
    manager.register(
        version=1,
        name="initial_schema",
        description="Create skill_adoptions table with indexes",
        up=migration_1_up
    )
    
    return manager
