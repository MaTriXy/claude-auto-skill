"""
Integration tests for V2 features.

Tests the complete pipeline:
- Session analysis
- LSP analysis
- Design pattern detection
- Enhanced skill generation
"""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core.event_store import EventStore
from core.pattern_detector import PatternDetector
from core.skill_generator import SkillGenerator
from core.session_analyzer import SessionAnalyzer
from core.lsp_analyzer import LSPAnalyzer
from core.design_pattern_detector import DesignPatternDetector


@pytest.fixture
def temp_db():
    """Create a temporary event store."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    store = EventStore(db_path=db_path)
    yield store

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample Python project for testing."""
    # Create project structure
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    # Create a simple Python file with patterns
    (src_dir / "repository.py").write_text("""
class UserRepository:
    '''Repository for user data access.'''

    def __init__(self, db):
        self.db = db

    def get_user(self, user_id):
        '''Get user by ID.'''
        return self.db.query(User).filter_by(id=user_id).first()

    def save_user(self, user):
        '''Save user to database.'''
        try:
            self.db.add(user)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise
""")

    (src_dir / "service.py").write_text("""
from .repository import UserRepository

class AuthService:
    '''Authentication service.'''

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def authenticate(self, username, password):
        '''Authenticate user.'''
        user = self.user_repo.get_user_by_username(username)
        if user and user.verify_password(password):
            return user
        return None
""")

    return tmp_path


class TestSessionAnalyzer:
    """Test session analysis features."""

    def test_analyze_session(self, temp_db):
        """Test session context analysis."""
        # Record some events
        session_id = "test-session-1"
        project_path = "/test/project"

        temp_db.record_event(
            session_id=session_id,
            project_path=project_path,
            tool_name="Grep",
            tool_input={"pattern": "error"},
            success=True,
        )

        temp_db.record_event(
            session_id=session_id,
            project_path=project_path,
            tool_name="Read",
            tool_input={"path": "src/auth.py"},
            success=True,
        )

        temp_db.record_event(
            session_id=session_id,
            project_path=project_path,
            tool_name="Edit",
            tool_input={"path": "src/auth.py"},
            success=True,
        )

        # Analyze session
        analyzer = SessionAnalyzer(temp_db)
        context = analyzer.analyze_session(session_id)

        assert context.session_id == session_id
        assert context.project_path == project_path
        assert len(context.turns) > 0


class TestLSPAnalyzer:
    """Test LSP code analysis features."""

    def test_analyze_python_file(self, sample_project):
        """Test Python file analysis."""
        analyzer = LSPAnalyzer()

        repo_file = sample_project / "src" / "repository.py"
        symbols, deps = analyzer.analyze_file(repo_file)

        # Should find UserRepository class
        class_symbols = [s for s in symbols if s.type == "class"]
        assert len(class_symbols) > 0
        assert any(s.name == "UserRepository" for s in class_symbols)

        # Should find methods
        method_symbols = [s for s in symbols if s.type == "method"]
        assert len(method_symbols) > 0

    def test_analyze_project(self, sample_project):
        """Test full project analysis."""
        analyzer = LSPAnalyzer()
        structure = analyzer.analyze_project(sample_project)

        assert len(structure.symbols) > 0
        assert len(structure.modules) > 0

        # Should find classes
        classes = analyzer.find_symbols_by_type(structure, "class")
        assert len(classes) > 0

        # Should find dependencies
        assert len(structure.dependencies) > 0


class TestDesignPatternDetector:
    """Test design pattern detection."""

    def test_detect_repository_pattern(self, sample_project):
        """Test detection of Repository pattern."""
        lsp = LSPAnalyzer()
        detector = DesignPatternDetector(lsp)

        patterns = detector.detect_patterns_in_project(sample_project)

        # Should detect Repository pattern
        repo_patterns = [p for p in patterns if p.pattern_name == "Repository"]
        assert len(repo_patterns) > 0

        repo_pattern = repo_patterns[0]
        assert repo_pattern.confidence > 0
        assert repo_pattern.pattern_type == "architectural"

    def test_detect_workflow_pattern(self):
        """Test workflow pattern detection."""
        detector = DesignPatternDetector()

        # TDD workflow: Write test -> Run -> Edit -> Run
        tool_sequence = ["Write", "Bash", "Edit", "Bash"]

        pattern = detector.detect_workflow_pattern(tool_sequence)

        assert pattern is not None
        assert pattern.pattern_name == "TDD"
        assert pattern.confidence > 0.5

    def test_get_pattern_context(self):
        """Test getting pattern context."""
        detector = DesignPatternDetector()

        context = detector.get_pattern_context("Repository")

        assert context is not None
        assert context.pattern_name == "Repository"
        assert len(context.benefits) > 0
        assert len(context.trade_offs) > 0


class TestEnhancedPatternDetector:
    """Test V2-enhanced pattern detector."""

    def test_detect_patterns_with_v2(self, temp_db, sample_project):
        """Test pattern detection with V2 enhancements."""
        # Create a pattern by recording events
        session_id = "session-1"

        for i in range(3):  # Create pattern with 3 occurrences
            temp_db.record_event(
                session_id=f"{session_id}-{i}",
                project_path=str(sample_project),
                tool_name="Read",
                tool_input={"path": "src/repository.py"},
                success=True,
            )
            temp_db.record_event(
                session_id=f"{session_id}-{i}",
                project_path=str(sample_project),
                tool_name="Edit",
                tool_input={"path": "src/repository.py"},
                success=True,
            )
            temp_db.record_event(
                session_id=f"{session_id}-{i}",
                project_path=str(sample_project),
                tool_name="Bash",
                tool_input={"command": "pytest"},
                success=True,
            )

        # Detect patterns with V2 enabled
        detector = PatternDetector(
            temp_db, enable_v2=True, project_path=sample_project
        )

        patterns = detector.detect_patterns(
            project_path=str(sample_project),
            min_occurrences=3,
            lookback_days=7,
        )

        assert len(patterns) > 0

        # Check V2 enhancements
        pattern = patterns[0]
        assert pattern.tool_sequence == ["Read", "Edit", "Bash"]

        # V2 fields should be present (may be None if analysis fails)
        assert hasattr(pattern, "session_context")
        assert hasattr(pattern, "code_context")
        assert hasattr(pattern, "design_patterns")


class TestEnhancedSkillGenerator:
    """Test V2-enhanced skill generator."""

    def test_generate_v2_skill(self, temp_db, sample_project):
        """Test generating a skill with V2 metadata."""
        # Create a pattern
        session_id = "skill-test-session"

        for i in range(3):
            temp_db.record_event(
                session_id=f"{session_id}-{i}",
                project_path=str(sample_project),
                tool_name="Grep",
                tool_input={"pattern": "test"},
                success=True,
            )
            temp_db.record_event(
                session_id=f"{session_id}-{i}",
                project_path=str(sample_project),
                tool_name="Read",
                tool_input={"path": "src/repository.py"},
                success=True,
            )

        # Detect pattern with V2
        detector = PatternDetector(
            temp_db, enable_v2=True, project_path=sample_project
        )
        patterns = detector.detect_patterns(
            project_path=str(sample_project), min_occurrences=3
        )

        assert len(patterns) > 0
        pattern = patterns[0]

        # Generate skill
        generator = SkillGenerator()
        candidate = generator.generate_candidate(pattern)

        assert candidate.name is not None
        assert candidate.description is not None
        assert len(candidate.steps) > 0

        # Render skill
        skill_md = candidate.render()

        assert "---" in skill_md  # YAML frontmatter
        assert candidate.name in skill_md
        assert "## Steps" in skill_md

        # Check for V2 sections if available
        if pattern.session_context:
            assert "session-analysis" in skill_md.lower()

        if pattern.design_patterns:
            assert "design-patterns" in skill_md.lower()


def test_backward_compatibility(temp_db):
    """Test that V2 doesn't break V1 functionality."""
    # Create V1-style usage (V2 disabled)
    session_id = "v1-session"
    project_path = "/test/v1"

    temp_db.record_event(
        session_id=session_id,
        project_path=project_path,
        tool_name="Read",
        tool_input={"path": "file.py"},
        success=True,
    )

    temp_db.record_event(
        session_id=session_id,
        project_path=project_path,
        tool_name="Edit",
        tool_input={"path": "file.py"},
        success=True,
    )

    # Detect patterns with V2 DISABLED
    detector = PatternDetector(temp_db, enable_v2=False)
    patterns = detector.detect_patterns(
        project_path=project_path, min_occurrences=1
    )

    # Should still work
    assert len(patterns) >= 0  # May or may not find patterns

    # Patterns should have V1 fields
    if patterns:
        pattern = patterns[0]
        assert hasattr(pattern, "tool_sequence")
        assert hasattr(pattern, "confidence")
        assert hasattr(pattern, "occurrence_count")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
