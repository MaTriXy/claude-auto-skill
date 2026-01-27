"""
Edge case tests for Auto-Skill components.

Tests error conditions, boundary values, and unusual inputs.
"""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from core import EventStore, PatternDetector, SkillGenerator, DetectedPattern
from core.unified_suggester import UnifiedSuggester
from core.skill_tracker import SkillTracker
from core.skillssh_client import SkillsShClient


class TestEventStoreEdgeCases:
    """Test EventStore edge cases."""
    
    def test_empty_database(self, tmp_path):
        """Test operations on empty database."""
        store = EventStore(db_path=tmp_path / "test.db")
        
        sequences = store.get_tool_sequences(lookback_days=7)
        assert sequences == []
        
        events = store.get_events_with_inputs(lookback_days=7)
        assert events == []
    
    def test_corrupted_metadata(self, tmp_path):
        """Test handling of corrupted JSON metadata."""
        store = EventStore(db_path=tmp_path / "test.db")
        
        # Manually insert event with invalid JSON
        with sqlite3.connect(store.db_path) as conn:
            conn.execute("""
                INSERT INTO tool_events (session_id, tool_name, timestamp, success, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, ("sess1", "Read", datetime.now(timezone.utc).isoformat(), 1, "{invalid json"))
            conn.commit()
        
        # Should handle gracefully
        events = store.get_events_with_inputs(lookback_days=7)
        assert len(events) > 0
        # metadata should be None or empty dict when parse fails
    
    def test_very_long_session(self, tmp_path):
        """Test handling sessions with many events (1000+)."""
        store = EventStore(db_path=tmp_path / "test.db")
        
        # Create a session with 1000 events
        session_id = "long_session"
        for i in range(1000):
            store.record_tool_use(
                session_id=session_id,
                tool_name="Read",
                success=True,
                metadata={"file": f"file_{i}.py"}
            )
        
        sequences = store.get_tool_sequences(lookback_days=7)
        assert len(sequences) == 1
        assert len(sequences[0]) == 1000
    
    def test_concurrent_writes(self, tmp_path):
        """Test concurrent writes to database."""
        store = EventStore(db_path=tmp_path / "test.db")
        
        # Simulate concurrent writes
        import threading
        
        def write_events(session_prefix):
            for i in range(10):
                store.record_tool_use(
                    session_id=f"{session_prefix}_{i}",
                    tool_name="Read",
                    success=True
                )
        
        threads = [
            threading.Thread(target=write_events, args=(f"thread_{i}",))
            for i in range(5)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have all 50 events
        sequences = store.get_tool_sequences(lookback_days=7)
        total_events = sum(len(seq) for seq in sequences)
        assert total_events == 50


class TestPatternDetectorEdgeCases:
    """Test PatternDetector edge cases."""
    
    def test_no_patterns(self, tmp_path):
        """Test detection when no patterns exist."""
        store = EventStore(db_path=tmp_path / "test.db")
        
        # Single event per session (no repetition)
        for i in range(5):
            store.record_tool_use(f"sess_{i}", "Read", True)
        
        detector = PatternDetector(store, enable_v2=False)
        patterns = detector.detect_patterns(min_occurrences=2)
        
        assert patterns == []
    
    def test_very_short_sequences(self, tmp_path):
        """Test detection with min_sequence_length=1."""
        store = EventStore(db_path=tmp_path / "test.db")
        
        # Single tool repeated
        for i in range(5):
            store.record_tool_use(f"sess_{i}", "Read", True)
        
        detector = PatternDetector(store, enable_v2=False)
        patterns = detector.detect_patterns(
            min_sequence_length=1,
            min_occurrences=3
        )
        
        assert len(patterns) >= 1
    
    def test_very_long_sequences(self, tmp_path):
        """Test detection with sequences longer than max_sequence_length."""
        store = EventStore(db_path=tmp_path / "test.db")
        
        # Create sessions with 20 different tools
        tools = [f"Tool{i}" for i in range(20)]
        for i in range(3):
            session_id = f"sess_{i}"
            for tool in tools:
                store.record_tool_use(session_id, tool, True)
        
        detector = PatternDetector(store, enable_v2=False)
        patterns = detector.detect_patterns(
            max_sequence_length=10,
            min_occurrences=2
        )
        
        # Should find patterns up to length 10
        if patterns:
            for pattern in patterns:
                assert len(pattern.tool_sequence) <= 10
    
    def test_all_failed_tools(self, tmp_path):
        """Test detection when all tools fail."""
        store = EventStore(db_path=tmp_path / "test.db")
        
        # All tools fail
        for i in range(3):
            session_id = f"sess_{i}"
            store.record_tool_use(session_id, "Read", False)
            store.record_tool_use(session_id, "Edit", False)
        
        detector = PatternDetector(store, enable_v2=False)
        patterns = detector.detect_patterns(min_occurrences=2)
        
        # Should still detect patterns but with low success_rate
        if patterns:
            assert patterns[0].success_rate < 0.5


class TestSkillGeneratorEdgeCases:
    """Test SkillGenerator edge cases."""
    
    def test_empty_tool_sequence(self, tmp_path):
        """Test generation with empty tool sequence."""
        pattern = DetectedPattern(
            id="test",
            tool_sequence=[],
            occurrence_count=1,
            confidence=0.8,
            session_ids=["sess1"],
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc)
        )
        
        generator = SkillGenerator(output_dir=tmp_path)
        candidate = generator.generate_candidate(pattern)
        
        # Should handle gracefully
        assert candidate.name
        assert candidate.description
    
    def test_very_long_tool_sequence(self, tmp_path):
        """Test generation with very long tool sequence (50+ tools)."""
        pattern = DetectedPattern(
            id="test",
            tool_sequence=[f"Tool{i}" for i in range(50)],
            occurrence_count=1,
            confidence=0.8,
            session_ids=["sess1"],
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc)
        )
        
        generator = SkillGenerator(output_dir=tmp_path)
        candidate = generator.generate_candidate(pattern)
        
        # Should generate valid skill
        assert len(candidate.steps) == 50
    
    def test_special_characters_in_names(self, tmp_path):
        """Test generation with special characters in pattern names."""
        pattern = DetectedPattern(
            id="test",
            tool_sequence=["Read", "Edit"],
            occurrence_count=1,
            confidence=0.8,
            session_ids=["sess1"],
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            suggested_name="test@#$%workflow"
        )
        
        generator = SkillGenerator(output_dir=tmp_path)
        candidate = generator.generate_candidate(pattern)
        
        # Name should be sanitized
        assert "@" not in candidate.name
        assert "#" not in candidate.name
        assert "$" not in candidate.name


class TestSkillTrackerEdgeCases:
    """Test SkillTracker edge cases."""
    
    def test_negative_confidence(self, tmp_path):
        """Test confidence calculation doesn't go negative."""
        tracker = SkillTracker(db_path=tmp_path / "test.db")
        
        # All failures
        for i in range(10):
            tracker.record_skill_usage("test-skill", "Test", "external", False)
        
        adoption = tracker.get_adoption("test-skill")
        assert adoption.current_confidence >= 0.0
    
    def test_confidence_cap(self, tmp_path):
        """Test confidence doesn't exceed 100%."""
        tracker = SkillTracker(db_path=tmp_path / "test.db")
        
        # All successes
        for i in range(100):
            tracker.record_skill_usage("test-skill", "Test", "external", True)
        
        adoption = tracker.get_adoption("test-skill")
        assert adoption.current_confidence <= 1.0
    
    def test_zero_usage(self, tmp_path):
        """Test handling of skills with zero usage."""
        tracker = SkillTracker(db_path=tmp_path / "test.db")
        
        adoption = tracker.get_adoption("nonexistent")
        assert adoption is None
    
    def test_graduation_with_mixed_results(self, tmp_path):
        """Test graduation criteria with mixed success/failure."""
        tracker = SkillTracker(db_path=tmp_path / "test.db")
        
        # 5 successes, 2 failures (71% success rate)
        for i in range(5):
            tracker.record_skill_usage("test-skill", "Test", "external", True)
        for i in range(2):
            tracker.record_skill_usage("test-skill", "Test", "external", False)
        
        # Should not graduate (needs 80% success rate)
        assert not tracker.should_graduate_to_local("test-skill")


class TestUnifiedSuggesterEdgeCases:
    """Test UnifiedSuggester edge cases."""
    
    def test_no_sources_enabled(self, tmp_path):
        """Test suggester with all sources disabled."""
        suggester = UnifiedSuggester(
            project_path=tmp_path,
            enable_mental=False,
            enable_external=False
        )
        
        suggestions = suggester.suggest_for_context([], {})
        # Should still work, just no suggestions
        assert isinstance(suggestions, list)
    
    def test_duplicate_suggestions(self, tmp_path):
        """Test deduplication of similar suggestions."""
        suggester = UnifiedSuggester(project_path=tmp_path)
        
        # Create patterns with similar names
        patterns = [
            DetectedPattern(
                id="test1",
                tool_sequence=["Read", "Edit"],
                occurrence_count=1,
                confidence=0.8,
                session_ids=["sess1"],
                first_seen=datetime.now(timezone.utc),
                last_seen=datetime.now(timezone.utc),
                suggested_name="test-workflow"
            ),
            DetectedPattern(
                id="test2",
                tool_sequence=["Read", "Edit"],
                occurrence_count=1,
                confidence=0.9,
                session_ids=["sess2"],
                first_seen=datetime.now(timezone.utc),
                last_seen=datetime.now(timezone.utc),
                suggested_name="test_workflow"  # Underscore vs hyphen
            ),
        ]
        
        suggestions = suggester.suggest_for_context(patterns, {})
        
        # Should deduplicate (keeping higher confidence)
        names = [s.name for s in suggestions]
        assert len(names) == len(set(names))  # All unique


class TestSkillsShClientEdgeCases:
    """Test SkillsShClient edge cases."""
    
    @pytest.mark.requires_network
    def test_empty_search_query(self):
        """Test search with empty query."""
        client = SkillsShClient()
        skills = client.search("", limit=5)
        
        # Should return empty or handle gracefully
        assert isinstance(skills, list)
    
    @pytest.mark.requires_network
    def test_very_long_search_query(self):
        """Test search with very long query."""
        client = SkillsShClient()
        query = "a" * 1000
        skills = client.search(query, limit=5)
        
        # Should handle without crashing
        assert isinstance(skills, list)
    
    def test_timeout(self):
        """Test request timeout handling."""
        client = SkillsShClient(timeout=0.001)  # 1ms timeout
        
        # Should fail fast and return empty list
        skills = client.search("test", limit=5)
        assert skills == []
    
    @pytest.mark.requires_network
    def test_invalid_skill_id(self):
        """Test fetching skill with invalid ID."""
        client = SkillsShClient()
        skill = client.get_skill_details("nonexistent-invalid-id-12345")
        
        # Should return None
        assert skill is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
