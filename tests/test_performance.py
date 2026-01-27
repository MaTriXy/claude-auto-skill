"""
Performance tests for Auto-Skill components.

Tests performance with realistic data volumes.
"""

import pytest
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from core import EventStore, PatternDetector, SkillGenerator


@pytest.mark.slow
class TestEventStorePerformance:
    """Test EventStore performance."""
    
    def test_insert_1000_events(self, tmp_path):
        """Test inserting 1000 events."""
        store = EventStore(db_path=tmp_path / "test.db")
        
        start = time.time()
        
        for i in range(1000):
            store.record_tool_use(
                session_id=f"sess_{i % 100}",  # 100 sessions
                tool_name="Read",
                success=True,
                metadata={"file": f"file_{i}.py"}
            )
        
        elapsed = time.time() - start
        
        # Should complete in < 5 seconds
        assert elapsed < 5.0
        print(f"\n  Insert 1000 events: {elapsed:.2f}s")
    
    def test_query_large_dataset(self, tmp_path):
        """Test querying with 10,000 events."""
        store = EventStore(db_path=tmp_path / "test.db")
        
        # Insert 10,000 events
        for i in range(10000):
            store.record_tool_use(
                session_id=f"sess_{i % 1000}",
                tool_name="Read",
                success=True
            )
        
        # Query
        start = time.time()
        sequences = store.get_tool_sequences(lookback_days=7)
        elapsed = time.time() - start
        
        # Should complete in < 2 seconds
        assert elapsed < 2.0
        assert len(sequences) == 1000
        print(f"\n  Query 10,000 events: {elapsed:.2f}s")


@pytest.mark.slow
class TestPatternDetectorPerformance:
    """Test PatternDetector performance."""
    
    def test_detect_patterns_100_sessions(self, tmp_path):
        """Test pattern detection with 100 sessions."""
        store = EventStore(db_path=tmp_path / "test.db")
        
        # Create 100 sessions with varying patterns
        for i in range(100):
            session_id = f"sess_{i}"
            # Create sequences of 5 tools
            for tool in ["Read", "Edit", "Bash", "Read", "Edit"]:
                store.record_tool_use(session_id, tool, True)
        
        detector = PatternDetector(store, enable_v2=False)
        
        start = time.time()
        patterns = detector.detect_patterns(min_occurrences=10)
        elapsed = time.time() - start
        
        # Should complete in < 3 seconds
        assert elapsed < 3.0
        print(f"\n  Detect patterns (100 sessions): {elapsed:.2f}s")
    
    def test_v2_analysis_performance(self, tmp_path):
        """Test V2 analysis overhead."""
        store = EventStore(db_path=tmp_path / "test.db")
        
        # Create 50 sessions
        for i in range(50):
            session_id = f"sess_{i}"
            for tool in ["Read", "Edit"]:
                store.record_tool_use(session_id, tool, True)
        
        # V1 (baseline)
        detector_v1 = PatternDetector(store, enable_v2=False)
        start = time.time()
        patterns_v1 = detector_v1.detect_patterns(min_occurrences=5)
        v1_time = time.time() - start
        
        # V2 (with analysis)
        detector_v2 = PatternDetector(store, enable_v2=True, enable_mental=False)
        start = time.time()
        patterns_v2 = detector_v2.detect_patterns(min_occurrences=5)
        v2_time = time.time() - start
        
        # V2 should be < 3x slower than V1
        assert v2_time < v1_time * 3
        print(f"\n  V1: {v1_time:.2f}s, V2: {v2_time:.2f}s (overhead: {v2_time/v1_time:.1f}x)")


@pytest.mark.slow
class TestSkillGeneratorPerformance:
    """Test SkillGenerator performance."""
    
    def test_generate_100_skills(self, tmp_path):
        """Test generating 100 skills."""
        from core import DetectedPattern
        
        generator = SkillGenerator(output_dir=tmp_path)
        
        # Create 100 patterns
        patterns = []
        for i in range(100):
            pattern = DetectedPattern(
                id=f"pattern_{i}",
                tool_sequence=["Read", "Edit", "Bash"],
                occurrence_count=5,
                confidence=0.8,
                session_ids=[f"sess_{j}" for j in range(5)],
                first_seen=datetime.now(timezone.utc),
                last_seen=datetime.now(timezone.utc)
            )
            patterns.append(pattern)
        
        # Generate all skills
        start = time.time()
        for pattern in patterns:
            candidate = generator.generate_candidate(pattern)
        elapsed = time.time() - start
        
        # Should complete in < 5 seconds
        assert elapsed < 5.0
        print(f"\n  Generate 100 skills: {elapsed:.2f}s ({elapsed/100*1000:.1f}ms each)")


@pytest.mark.slow
class TestEndToEndPerformance:
    """Test end-to-end performance."""
    
    def test_full_workflow_100_sessions(self, tmp_path):
        """Test complete workflow with 100 sessions."""
        store = EventStore(db_path=tmp_path / "test.db")
        
        # 1. Record events (100 sessions, 5 tools each)
        start = time.time()
        for i in range(100):
            session_id = f"sess_{i}"
            for tool in ["Read", "Edit", "Bash", "Read", "Edit"]:
                store.record_tool_use(session_id, tool, True)
        record_time = time.time() - start
        
        # 2. Detect patterns
        detector = PatternDetector(store, enable_v2=True, enable_mental=False)
        start = time.time()
        patterns = detector.detect_patterns(min_occurrences=10)
        detect_time = time.time() - start
        
        # 3. Generate skills
        generator = SkillGenerator(output_dir=tmp_path)
        start = time.time()
        for pattern in patterns[:10]:  # Generate top 10
            candidate = generator.generate_candidate(pattern)
        generate_time = time.time() - start
        
        total_time = record_time + detect_time + generate_time
        
        # Should complete in < 10 seconds
        assert total_time < 10.0
        
        print(f"\n  Full workflow:")
        print(f"    Record: {record_time:.2f}s")
        print(f"    Detect: {detect_time:.2f}s")
        print(f"    Generate: {generate_time:.2f}s")
        print(f"    Total: {total_time:.2f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "slow"])
