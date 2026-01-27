"""
Skill Adoption Tracker - Tracks usage of external skills and confidence evolution.

Tracks skill adoption lifecycle:
1. External skill discovered (50% confidence)
2. Usage tracked (confidence increases with success rate)
3. Graduation to local skill (85%+ confidence, 5+ uses, 80%+ success)

Confidence Evolution:
- External: Start at 50%
- Proven: Reach 75% (3+ uses, 70%+ success)
- Local: Graduate at 85% (5+ uses, 80%+ success)
"""

import sqlite3
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SkillAdoption:
    """Tracks adoption of a skill (external or local)."""

    skill_id: str
    skill_name: str
    source: str  # "external", "local", "mental-hint"
    initial_confidence: float  # Starting confidence
    current_confidence: float  # Current confidence (evolves with usage)
    usage_count: int
    success_count: int
    failure_count: int
    first_used: datetime
    last_used: datetime
    graduated_to_local: bool = False  # True if promoted to local skill

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.usage_count == 0:
            return 0.0
        return self.success_count / self.usage_count

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "source": self.source,
            "initial_confidence": self.initial_confidence,
            "current_confidence": self.current_confidence,
            "usage_count": self.usage_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_rate,
            "first_used": self.first_used.isoformat(),
            "last_used": self.last_used.isoformat(),
            "graduated_to_local": self.graduated_to_local
        }


class SkillTracker:
    """
    Tracks skill adoption and evolution.

    Uses SQLite to persist skill usage data and calculate confidence scores
    based on usage patterns and success rates.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize skill tracker.

        Args:
            db_path: Path to SQLite database (default: ~/.claude/auto-skill/skills_tracking.db)
        """
        if db_path is None:
            db_path = Path.home() / ".claude" / "auto-skill" / "skills_tracking.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
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
            conn.commit()

    def record_skill_usage(
        self,
        skill_id: str,
        skill_name: str,
        source: str,
        success: bool
    ):
        """
        Record a skill usage event.

        Updates confidence score based on usage patterns and success rate.

        Args:
            skill_id: Unique skill identifier
            skill_name: Human-readable skill name
            source: Source of skill ("external", "local", "mental-hint")
            success: Whether the skill usage was successful
        """
        now = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            # Check if skill exists
            cursor = conn.execute(
                "SELECT * FROM skill_adoptions WHERE skill_id = ?",
                (skill_id,)
            )
            row = cursor.fetchone()

            if row:
                # Update existing
                usage_count = row[5] + 1
                success_count = row[6] + (1 if success else 0)
                failure_count = row[7] + (0 if success else 1)

                # Calculate new confidence
                success_rate = success_count / usage_count if usage_count > 0 else 0
                current_confidence = self._calculate_confidence(
                    initial=row[3],
                    source=row[2],
                    usage_count=usage_count,
                    success_rate=success_rate
                )

                conn.execute("""
                    UPDATE skill_adoptions
                    SET usage_count = ?,
                        success_count = ?,
                        failure_count = ?,
                        current_confidence = ?,
                        last_used = ?,
                        updated_at = ?
                    WHERE skill_id = ?
                """, (usage_count, success_count, failure_count, current_confidence, now, now, skill_id))

            else:
                # Insert new
                initial_confidence = self._get_initial_confidence(source)
                conn.execute("""
                    INSERT INTO skill_adoptions
                    (skill_id, skill_name, source, initial_confidence, current_confidence,
                     usage_count, success_count, failure_count, first_used, last_used)
                    VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
                """, (
                    skill_id, skill_name, source, initial_confidence, initial_confidence,
                    1 if success else 0, 0 if success else 1, now, now
                ))

            conn.commit()

    def _get_initial_confidence(self, source: str) -> float:
        """
        Get initial confidence based on source.

        Args:
            source: Source of skill

        Returns:
            Initial confidence score
        """
        confidence_map = {
            "external": 0.5,      # External skills start at 50%
            "mental-hint": 0.6,   # Mental hints start at 60%
            "local": 0.8          # Local patterns start at 80%
        }
        return confidence_map.get(source, 0.5)

    def _calculate_confidence(
        self,
        initial: float,
        source: str,
        usage_count: int,
        success_rate: float
    ) -> float:
        """
        Calculate confidence based on usage and success.

        Confidence evolution:
        - Starts at initial confidence
        - Increases with successful usage
        - Capped at 0.95 for external, 1.0 for local

        Args:
            initial: Initial confidence
            source: Source of skill
            usage_count: Total usage count
            success_rate: Success rate (0.0 to 1.0)

        Returns:
            Updated confidence score
        """
        # Usage factor: more uses = higher confidence (cap at 10 uses)
        usage_factor = min(usage_count / 10.0, 1.0)

        # Weighted combination: 70% success rate, 30% usage count
        weighted_confidence = (success_rate * 0.7) + (usage_factor * 0.3)

        # Blend with initial confidence (30% initial, 70% weighted)
        new_confidence = (initial * 0.3) + (weighted_confidence * 0.7)

        # Cap based on source
        max_confidence = 0.95 if source == "external" else 1.0

        return min(new_confidence, max_confidence)

    def get_adoption(self, skill_id: str) -> Optional[SkillAdoption]:
        """
        Get adoption details for a skill.

        Args:
            skill_id: Skill identifier

        Returns:
            SkillAdoption object if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM skill_adoptions WHERE skill_id = ?",
                (skill_id,)
            )
            row = cursor.fetchone()

            if row:
                return SkillAdoption(
                    skill_id=row[0],
                    skill_name=row[1],
                    source=row[2],
                    initial_confidence=row[3],
                    current_confidence=row[4],
                    usage_count=row[5],
                    success_count=row[6],
                    failure_count=row[7],
                    first_used=datetime.fromisoformat(row[8]),
                    last_used=datetime.fromisoformat(row[9]),
                    graduated_to_local=bool(row[10])
                )

            return None

    def get_all_adoptions(self, min_confidence: float = 0.0) -> list[SkillAdoption]:
        """
        Get all skill adoptions above minimum confidence.

        Args:
            min_confidence: Minimum confidence threshold

        Returns:
            List of SkillAdoption objects
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM skill_adoptions
                WHERE current_confidence >= ?
                ORDER BY current_confidence DESC, usage_count DESC
            """, (min_confidence,))

            adoptions = []
            for row in cursor.fetchall():
                adoptions.append(SkillAdoption(
                    skill_id=row[0],
                    skill_name=row[1],
                    source=row[2],
                    initial_confidence=row[3],
                    current_confidence=row[4],
                    usage_count=row[5],
                    success_count=row[6],
                    failure_count=row[7],
                    first_used=datetime.fromisoformat(row[8]),
                    last_used=datetime.fromisoformat(row[9]),
                    graduated_to_local=bool(row[10])
                ))

            return adoptions

    def should_graduate_to_local(self, skill_id: str) -> bool:
        """
        Check if skill should be graduated to local.

        Graduation criteria:
        - Confidence >= 0.85
        - Used at least 5 times
        - Success rate >= 0.8
        - Not already graduated

        Args:
            skill_id: Skill identifier

        Returns:
            True if skill should graduate, False otherwise
        """
        adoption = self.get_adoption(skill_id)

        if not adoption or adoption.graduated_to_local:
            return False

        # Only external skills can graduate
        if adoption.source != "external":
            return False

        # Check graduation criteria
        return (
            adoption.current_confidence >= 0.85
            and adoption.usage_count >= 5
            and adoption.success_rate >= 0.8
        )

    def mark_graduated(self, skill_id: str):
        """
        Mark skill as graduated to local.

        Args:
            skill_id: Skill identifier
        """
        now = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE skill_adoptions
                SET graduated_to_local = 1,
                    source = 'local',
                    current_confidence = 0.85,
                    updated_at = ?
                WHERE skill_id = ?
            """, (now, skill_id))
            conn.commit()

    def get_graduation_candidates(self) -> list[SkillAdoption]:
        """
        Get all skills that are candidates for graduation.

        Returns:
            List of SkillAdoption objects ready for graduation
        """
        adoptions = self.get_all_adoptions(min_confidence=0.80)
        return [
            adoption for adoption in adoptions
            if self.should_graduate_to_local(adoption.skill_id)
        ]
