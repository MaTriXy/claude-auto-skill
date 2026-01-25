"""
Event Store - SQLite persistence layer for tool events.

Stores tool usage events for pattern detection. Uses a hybrid scope model:
- Global storage: All events in ~/.claude/auto-skill/events.db
- Project tagging: Each event tagged with project_path for filtering
"""

import json
import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional


@dataclass
class ToolEvent:
    """Represents a single tool invocation event."""

    id: str
    session_id: str
    project_path: str
    tool_name: str
    tool_input: dict
    tool_response: Optional[str]
    success: bool
    timestamp: datetime

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "project_path": self.project_path,
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "tool_response": self.tool_response,
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
        }


class EventStore:
    """SQLite-backed event storage for tool usage patterns."""

    DEFAULT_DB_PATH = Path.home() / ".claude" / "auto-skill" / "events.db"

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the event store.

        Args:
            db_path: Path to SQLite database. Defaults to ~/.claude/auto-skill/events.db
        """
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._init_db()

    def _init_db(self) -> None:
        """Create database schema if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    project_path TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    tool_input TEXT NOT NULL,
                    tool_response TEXT,
                    success INTEGER NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_id ON events(session_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_project_path ON events(project_path)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tool_name ON events(tool_name)
            """)
            conn.commit()

    def record_event(
        self,
        session_id: str,
        project_path: str,
        tool_name: str,
        tool_input: dict,
        tool_response: Optional[str] = None,
        success: bool = True,
    ) -> ToolEvent:
        """
        Record a tool usage event.

        Args:
            session_id: Current Claude session ID
            project_path: Path to the project being worked on
            tool_name: Name of the tool that was called
            tool_input: Input parameters to the tool
            tool_response: Response from the tool (truncated if large)
            success: Whether the tool call succeeded

        Returns:
            The recorded ToolEvent
        """
        event = ToolEvent(
            id=str(uuid.uuid4()),
            session_id=session_id,
            project_path=project_path,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_response=self._truncate_response(tool_response),
            success=success,
            timestamp=datetime.now(timezone.utc),
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO events (id, session_id, project_path, tool_name,
                                   tool_input, tool_response, success, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.id,
                    event.session_id,
                    event.project_path,
                    event.tool_name,
                    json.dumps(event.tool_input),
                    event.tool_response,
                    1 if event.success else 0,
                    event.timestamp.isoformat(),
                ),
            )
            conn.commit()

        return event

    def _truncate_response(self, response: Optional[str], max_length: int = 1000) -> Optional[str]:
        """Truncate large responses to save storage space."""
        if response is None:
            return None
        if len(response) <= max_length:
            return response
        return response[:max_length] + "...[truncated]"

    def get_session_events(self, session_id: str) -> list[ToolEvent]:
        """Get all events for a specific session, ordered by timestamp."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM events
                WHERE session_id = ?
                ORDER BY timestamp ASC
                """,
                (session_id,),
            )
            return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_tool_sequences(
        self,
        project_path: Optional[str] = None,
        lookback_days: int = 7,
        min_sequence_length: int = 2,
    ) -> list[list[str]]:
        """
        Get tool sequences from sessions, grouped by session.

        Args:
            project_path: Filter to specific project (None for all projects)
            lookback_days: How many days back to look
            min_sequence_length: Minimum number of tools in a sequence

        Returns:
            List of tool name sequences (one per session)
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)

        query = """
            SELECT session_id, tool_name
            FROM events
            WHERE timestamp > ?
        """
        params = [cutoff.isoformat()]

        if project_path:
            query += " AND project_path = ?"
            params.append(project_path)

        query += " ORDER BY session_id, timestamp ASC"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)

            sequences = []
            current_session = None
            current_sequence = []

            for row in cursor.fetchall():
                session_id, tool_name = row
                if session_id != current_session:
                    if len(current_sequence) >= min_sequence_length:
                        sequences.append(current_sequence)
                    current_session = session_id
                    current_sequence = []
                current_sequence.append(tool_name)

            # Don't forget the last session
            if len(current_sequence) >= min_sequence_length:
                sequences.append(current_sequence)

            return sequences

    def get_events_with_inputs(
        self,
        project_path: Optional[str] = None,
        lookback_days: int = 7,
    ) -> list[list[ToolEvent]]:
        """
        Get full events (including inputs) grouped by session.

        Useful for more sophisticated pattern matching that considers inputs.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)

        query = """
            SELECT * FROM events
            WHERE timestamp > ?
        """
        params = [cutoff.isoformat()]

        if project_path:
            query += " AND project_path = ?"
            params.append(project_path)

        query += " ORDER BY session_id, timestamp ASC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)

            sessions = []
            current_session = None
            current_events = []

            for row in cursor.fetchall():
                event = self._row_to_event(row)
                if event.session_id != current_session:
                    if current_events:
                        sessions.append(current_events)
                    current_session = event.session_id
                    current_events = []
                current_events.append(event)

            if current_events:
                sessions.append(current_events)

            return sessions

    def get_stats(self) -> dict:
        """Get basic statistics about stored events."""
        with sqlite3.connect(self.db_path) as conn:
            total_events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            unique_sessions = conn.execute(
                "SELECT COUNT(DISTINCT session_id) FROM events"
            ).fetchone()[0]
            unique_projects = conn.execute(
                "SELECT COUNT(DISTINCT project_path) FROM events"
            ).fetchone()[0]

            # Most common tools
            tool_counts = conn.execute("""
                SELECT tool_name, COUNT(*) as count
                FROM events
                GROUP BY tool_name
                ORDER BY count DESC
                LIMIT 10
            """).fetchall()

            return {
                "total_events": total_events,
                "unique_sessions": unique_sessions,
                "unique_projects": unique_projects,
                "top_tools": [{"tool": t, "count": c} for t, c in tool_counts],
            }

    def _row_to_event(self, row: sqlite3.Row) -> ToolEvent:
        """Convert a database row to a ToolEvent."""
        return ToolEvent(
            id=row["id"],
            session_id=row["session_id"],
            project_path=row["project_path"],
            tool_name=row["tool_name"],
            tool_input=json.loads(row["tool_input"]),
            tool_response=row["tool_response"],
            success=bool(row["success"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
        )

    def cleanup_old_events(self, days: int = 30) -> int:
        """Delete events older than specified days. Returns count deleted."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM events WHERE timestamp < ?",
                (cutoff.isoformat(),),
            )
            conn.commit()
            return cursor.rowcount
