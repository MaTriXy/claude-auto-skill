"""
Tests for database migration system.
"""

import pytest
import sqlite3
from pathlib import Path
from core.migrations import (
    MigrationManager,
    Migration,
    MigrationError,
    create_event_store_migrations,
    create_skill_tracker_migrations,
)


class TestMigrationManager:
    """Test MigrationManager functionality."""
    
    def test_init_creates_migration_table(self, tmp_path):
        """Test that initialization creates schema_migrations table."""
        db_path = tmp_path / "test.db"
        manager = MigrationManager(db_path)
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
            )
            assert cursor.fetchone() is not None
    
    def test_get_current_version_empty_db(self, tmp_path):
        """Test get_current_version returns 0 for empty database."""
        db_path = tmp_path / "test.db"
        manager = MigrationManager(db_path)
        
        assert manager.get_current_version() == 0
    
    def test_register_migration(self, tmp_path):
        """Test registering a migration."""
        db_path = tmp_path / "test.db"
        manager = MigrationManager(db_path)
        
        def up(conn):
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        
        manager.register(
            version=1,
            name="test_migration",
            description="Test migration",
            up=up
        )
        
        assert len(manager.migrations) == 1
        assert manager.migrations[0].version == 1
        assert manager.migrations[0].name == "test_migration"
    
    def test_apply_migration(self, tmp_path):
        """Test applying a single migration."""
        db_path = tmp_path / "test.db"
        manager = MigrationManager(db_path)
        
        def up(conn):
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        
        manager.register(
            version=1,
            name="test_migration",
            description="Test migration",
            up=up
        )
        
        manager.migrate()
        
        # Check version was recorded
        assert manager.get_current_version() == 1
        
        # Check table was created
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='test'"
            )
            assert cursor.fetchone() is not None
    
    def test_apply_multiple_migrations(self, tmp_path):
        """Test applying multiple migrations in order."""
        db_path = tmp_path / "test.db"
        manager = MigrationManager(db_path)
        
        def up1(conn):
            conn.execute("CREATE TABLE test1 (id INTEGER PRIMARY KEY)")
        
        def up2(conn):
            conn.execute("CREATE TABLE test2 (id INTEGER PRIMARY KEY)")
        
        def up3(conn):
            conn.execute("CREATE TABLE test3 (id INTEGER PRIMARY KEY)")
        
        manager.register(1, "migration_1", "First", up1)
        manager.register(2, "migration_2", "Second", up2)
        manager.register(3, "migration_3", "Third", up3)
        
        manager.migrate()
        
        assert manager.get_current_version() == 3
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('test1', 'test2', 'test3')"
            )
            tables = [row[0] for row in cursor.fetchall()]
            assert set(tables) == {'test1', 'test2', 'test3'}
    
    def test_migrate_to_specific_version(self, tmp_path):
        """Test migrating to a specific version."""
        db_path = tmp_path / "test.db"
        manager = MigrationManager(db_path)
        
        def up1(conn):
            conn.execute("CREATE TABLE test1 (id INTEGER PRIMARY KEY)")
        
        def up2(conn):
            conn.execute("CREATE TABLE test2 (id INTEGER PRIMARY KEY)")
        
        manager.register(1, "migration_1", "First", up1)
        manager.register(2, "migration_2", "Second", up2)
        
        # Migrate only to version 1
        manager.migrate(target_version=1)
        
        assert manager.get_current_version() == 1
        
        with sqlite3.connect(db_path) as conn:
            # test1 should exist
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='test1'"
            )
            assert cursor.fetchone() is not None
            
            # test2 should not exist
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='test2'"
            )
            assert cursor.fetchone() is None
    
    def test_rollback_migration(self, tmp_path):
        """Test rolling back migrations."""
        db_path = tmp_path / "test.db"
        manager = MigrationManager(db_path)
        
        def up(conn):
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        
        def down(conn):
            conn.execute("DROP TABLE test")
        
        manager.register(1, "migration_1", "First", up, down)
        
        # Apply migration
        manager.migrate()
        assert manager.get_current_version() == 1
        
        # Rollback
        manager.rollback(target_version=0)
        assert manager.get_current_version() == 0
        
        # Table should not exist
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='test'"
            )
            assert cursor.fetchone() is None
    
    def test_rollback_without_down_fails(self, tmp_path):
        """Test rollback fails if migration doesn't have down()."""
        db_path = tmp_path / "test.db"
        manager = MigrationManager(db_path)
        
        def up(conn):
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        
        manager.register(1, "migration_1", "First", up)  # No down()
        
        manager.migrate()
        
        with pytest.raises(MigrationError, match="does not support rollback"):
            manager.rollback(target_version=0)
    
    def test_failed_migration_raises_error(self, tmp_path):
        """Test that failed migrations raise MigrationError."""
        db_path = tmp_path / "test.db"
        manager = MigrationManager(db_path)
        
        def up_fails(conn):
            raise ValueError("Intentional failure")
        
        manager.register(1, "bad_migration", "Will fail", up_fails)
        
        with pytest.raises(MigrationError, match="Failed to apply migration"):
            manager.migrate()
        
        # Version should not have been recorded
        assert manager.get_current_version() == 0
    
    def test_get_pending_migrations(self, tmp_path):
        """Test getting list of pending migrations."""
        db_path = tmp_path / "test.db"
        manager = MigrationManager(db_path)
        
        def up1(conn):
            conn.execute("CREATE TABLE test1 (id INTEGER PRIMARY KEY)")
        
        def up2(conn):
            conn.execute("CREATE TABLE test2 (id INTEGER PRIMARY KEY)")
        
        manager.register(1, "migration_1", "First", up1)
        manager.register(2, "migration_2", "Second", up2)
        
        # Both pending
        pending = manager.get_pending_migrations()
        assert len(pending) == 2
        
        # Apply first
        manager.migrate(target_version=1)
        
        # Only second pending
        pending = manager.get_pending_migrations()
        assert len(pending) == 1
        assert pending[0].version == 2


class TestEventStoreMigrations:
    """Test EventStore migrations."""
    
    def test_create_event_store_migrations(self, tmp_path):
        """Test creating EventStore migration manager."""
        db_path = tmp_path / "events.db"
        manager = create_event_store_migrations(db_path)
        
        assert len(manager.migrations) == 3
        assert manager.migrations[0].name == "initial_schema"
        assert manager.migrations[1].name == "add_inputs_column"
        assert manager.migrations[2].name == "add_project_index"
    
    def test_apply_all_event_store_migrations(self, tmp_path):
        """Test applying all EventStore migrations."""
        db_path = tmp_path / "events.db"
        manager = create_event_store_migrations(db_path)
        
        manager.migrate()
        
        assert manager.get_current_version() == 3
        
        # Check table exists
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='tool_events'"
            )
            assert cursor.fetchone() is not None
            
            # Check inputs column exists
            cursor = conn.execute("PRAGMA table_info(tool_events)")
            columns = [row[1] for row in cursor.fetchall()]
            assert 'inputs' in columns
            
            # Check indexes exist
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
            indexes = [row[0] for row in cursor.fetchall()]
            assert 'idx_session_id' in indexes
            assert 'idx_timestamp' in indexes
            assert 'idx_project_path' in indexes


class TestSkillTrackerMigrations:
    """Test SkillTracker migrations."""
    
    def test_create_skill_tracker_migrations(self, tmp_path):
        """Test creating SkillTracker migration manager."""
        db_path = tmp_path / "skills.db"
        manager = create_skill_tracker_migrations(db_path)
        
        assert len(manager.migrations) == 1
        assert manager.migrations[0].name == "initial_schema"
    
    def test_apply_skill_tracker_migrations(self, tmp_path):
        """Test applying SkillTracker migrations."""
        db_path = tmp_path / "skills.db"
        manager = create_skill_tracker_migrations(db_path)
        
        manager.migrate()
        
        assert manager.get_current_version() == 1
        
        # Check table exists
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='skill_adoptions'"
            )
            assert cursor.fetchone() is not None
            
            # Check indexes exist
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
            indexes = [row[0] for row in cursor.fetchall()]
            assert 'idx_confidence' in indexes
            assert 'idx_source' in indexes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
