"""
Telemetry Collector - Tracks skill usage metrics for effectiveness analysis.

Records per-skill usage events with timing, outcome, and agent context.
Provides aggregation queries for effectiveness reports.

Anonymous telemetry follows privacy-first principles:
- No PII collected (no usernames, IPs, file paths, or identifying data)
- No content capture (no search queries, file contents, or user input)
- Aggregate only (counts, timing, scores — not specific values)
- Fire-and-forget (daemon threads, silent failures, never blocks)
- Transparent opt-out via environment variables:
    export AUTO_SKILL_NO_TELEMETRY=1   # Tool-specific
    export DO_NOT_TRACK=1              # Universal standard
- Automatically disabled in CI environments
"""

import os
import platform
import sqlite3
import sys
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# --- Anonymous Telemetry Configuration ---

TELEMETRY_ENDPOINT = "https://t.insightx.pro"
TELEMETRY_VERSION = "3.0.1"
TOOL_ID = "auto-skill"

CI_VARS = [
    "CI", "GITHUB_ACTIONS", "GITLAB_CI", "CIRCLECI",
    "TRAVIS", "BUILDKITE", "JENKINS_URL",
]


def is_telemetry_disabled() -> bool:
    """Check if anonymous telemetry is disabled via env vars or CI."""
    if os.environ.get("AUTO_SKILL_NO_TELEMETRY"):
        return True
    if os.environ.get("DO_NOT_TRACK"):
        return True
    return any(os.environ.get(v) for v in CI_VARS)


def _send_anonymous(url: str) -> None:
    """Send anonymous telemetry event (internal, runs in background thread)."""
    try:
        req = Request(url, headers={"User-Agent": f"{TOOL_ID}/{TELEMETRY_VERSION}"})
        urlopen(req, timeout=2)
    except Exception:
        pass  # Silent failure — telemetry must never surface errors


def track(event: str, data: Optional[dict] = None) -> None:
    """Fire-and-forget anonymous telemetry. Never blocks, never fails.

    Args:
        event: Event name (e.g. "skill_used", "skill_generated", "search").
        data: Optional aggregate data (counts, timing, scores — never PII).
    """
    if is_telemetry_disabled():
        return

    try:
        payload = {
            "t": TOOL_ID,
            "e": event,
            "v": TELEMETRY_VERSION,
            "py": platform.python_version(),
            "os": sys.platform,
            **(data or {}),
        }
        url = f"{TELEMETRY_ENDPOINT}?{urlencode(payload)}"
        threading.Thread(target=_send_anonymous, args=(url,), daemon=True).start()
    except Exception:
        pass  # Silent failure


@dataclass
class TelemetryEvent:
    """A single skill usage telemetry event."""

    id: str
    skill_id: str
    skill_name: str
    session_id: str
    agent_id: str
    duration_ms: Optional[int]
    outcome: str  # "success", "failure", "partial", "skipped"
    timestamp: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "duration_ms": self.duration_ms,
            "outcome": self.outcome,
            "timestamp": self.timestamp,
        }


@dataclass
class EffectivenessReport:
    """Aggregated effectiveness data for a skill."""

    skill_name: str
    total_uses: int
    success_count: int
    failure_count: int
    success_rate: float
    avg_duration_ms: Optional[float]
    agents_used: list[str]
    last_used: str

    def to_dict(self) -> dict:
        return {
            "skill_name": self.skill_name,
            "total_uses": self.total_uses,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": round(self.success_rate, 3),
            "avg_duration_ms": round(self.avg_duration_ms) if self.avg_duration_ms else None,
            "agents_used": self.agents_used,
            "last_used": self.last_used,
        }


class TelemetryCollector:
    """Collects and queries skill usage telemetry.

    Stores data in a SQLite database for fast local queries.
    """

    DEFAULT_DB_PATH = Path.home() / ".claude" / "auto-skill" / "telemetry.db"

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
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
            conn.commit()

    def record_event(
        self,
        skill_id: str,
        skill_name: str,
        session_id: str,
        outcome: str,
        agent_id: str = "unknown",
        duration_ms: Optional[int] = None,
    ) -> TelemetryEvent:
        """Record a skill usage telemetry event.

        Args:
            skill_id: Skill identifier.
            skill_name: Human-readable skill name.
            session_id: Current session ID.
            outcome: One of "success", "failure", "partial", "skipped".
            agent_id: Agent that used the skill.
            duration_ms: Duration of skill execution in milliseconds.

        Returns:
            The recorded TelemetryEvent.
        """
        event = TelemetryEvent(
            id=str(uuid.uuid4()),
            skill_id=skill_id,
            skill_name=skill_name,
            session_id=session_id,
            agent_id=agent_id,
            duration_ms=duration_ms,
            outcome=outcome,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO skill_telemetry
                (id, skill_id, skill_name, session_id, agent_id, duration_ms, outcome, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.id,
                    event.skill_id,
                    event.skill_name,
                    event.session_id,
                    event.agent_id,
                    event.duration_ms,
                    event.outcome,
                    event.timestamp,
                ),
            )
            conn.commit()

        # Fire anonymous telemetry (aggregate data only, no PII)
        track("skill_used", {
            "outcome": event.outcome,
            "agent": event.agent_id,
            "ms": event.duration_ms or 0,
        })

        return event

    def get_effectiveness_report(
        self, skill_name: Optional[str] = None
    ) -> list[EffectivenessReport]:
        """Get effectiveness reports for skills.

        Args:
            skill_name: Optional filter to a specific skill.

        Returns:
            List of EffectivenessReport objects.
        """
        query = """
            SELECT
                skill_name,
                COUNT(*) as total_uses,
                SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN outcome = 'failure' THEN 1 ELSE 0 END) as failure_count,
                AVG(duration_ms) as avg_duration_ms,
                MAX(timestamp) as last_used
            FROM skill_telemetry
        """
        params = []

        if skill_name:
            query += " WHERE skill_name = ?"
            params.append(skill_name)

        query += " GROUP BY skill_name ORDER BY total_uses DESC"

        reports = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)

            for row in cursor.fetchall():
                name, total, success, failure, avg_dur, last = row
                success_rate = success / total if total > 0 else 0.0

                # Get unique agents
                agents_cursor = conn.execute(
                    "SELECT DISTINCT agent_id FROM skill_telemetry WHERE skill_name = ?",
                    (name,),
                )
                agents = [r[0] for r in agents_cursor.fetchall()]

                reports.append(
                    EffectivenessReport(
                        skill_name=name,
                        total_uses=total,
                        success_count=success,
                        failure_count=failure,
                        success_rate=success_rate,
                        avg_duration_ms=avg_dur,
                        agents_used=agents,
                        last_used=last,
                    )
                )

        return reports

    def get_events(
        self, skill_name: Optional[str] = None, limit: int = 100
    ) -> list[TelemetryEvent]:
        """Get raw telemetry events.

        Args:
            skill_name: Optional filter.
            limit: Maximum events to return.

        Returns:
            List of TelemetryEvent objects, newest first.
        """
        query = "SELECT * FROM skill_telemetry"
        params = []

        if skill_name:
            query += " WHERE skill_name = ?"
            params.append(skill_name)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        events = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            for row in cursor.fetchall():
                events.append(
                    TelemetryEvent(
                        id=row["id"],
                        skill_id=row["skill_id"],
                        skill_name=row["skill_name"],
                        session_id=row["session_id"],
                        agent_id=row["agent_id"],
                        duration_ms=row["duration_ms"],
                        outcome=row["outcome"],
                        timestamp=row["timestamp"],
                    )
                )

        return events
