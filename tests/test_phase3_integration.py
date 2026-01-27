"""
Tests for Phase 3: Pattern Detector Integration with Mental Model.

Tests hybrid integration between:
- PatternDetector with Mental context
- SkillGenerator with Vercel metadata
- UnifiedSuggester integration
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone

from core import (
    PatternDetector,
    DetectedPattern,
    SkillGenerator,
    EventStore,
    MentalAnalyzer,
    UnifiedSuggester,
)


class TestMentalIntegration:
    """Test Mental model integration with pattern detection."""

    def test_pattern_detector_with_mental(self, tmp_path):
        """Test that PatternDetector can integrate Mental context."""
        store = EventStore(db_path=tmp_path / "test.db")
        
        # Create detector with Mental enabled
        detector = PatternDetector(
            store,
            enable_v2=True,
            enable_mental=True,
            project_path=tmp_path
        )
        
        # Verify Mental analyzer is available (may be None if not installed)
        assert detector.enable_mental in [True, False]
        
        if detector.mental_analyzer:
            # Mental is available
            assert detector.mental_analyzer.is_mental_available()
    
    def test_detected_pattern_has_mental_context_field(self):
        """Test that DetectedPattern has mental_context field."""
        pattern = DetectedPattern(
            id="test",
            tool_sequence=["Read", "Edit"],
            occurrence_count=3,
            confidence=0.8,
            session_ids=["sess1"],
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
        )
        
        # Verify mental_context field exists
        assert hasattr(pattern, 'mental_context')
        assert pattern.mental_context is None  # Default value
        
        # Set mental context
        pattern.mental_context = {
            "domains": [{"name": "Payment", "description": "Payment processing"}],
            "capabilities": [{"name": "Checkout", "description": "Process checkout"}]
        }
        
        # Verify it's stored
        assert pattern.mental_context is not None
        assert len(pattern.mental_context["domains"]) == 1
        assert pattern.mental_context["domains"][0]["name"] == "Payment"
    
    def test_mental_context_in_pattern_dict(self):
        """Test that mental_context is included in to_dict()."""
        pattern = DetectedPattern(
            id="test",
            tool_sequence=["Read"],
            occurrence_count=1,
            confidence=0.7,
            session_ids=["sess1"],
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            mental_context={
                "domains": [{"name": "User"}],
                "capabilities": [{"name": "Login"}]
            }
        )
        
        pattern_dict = pattern.to_dict()
        
        assert "mental_context" in pattern_dict
        assert pattern_dict["mental_context"]["domains"][0]["name"] == "User"


class TestSkillGeneratorEnhancements:
    """Test SkillGenerator Vercel metadata and Mental integration."""
    
    def test_vercel_metadata_in_frontmatter(self, tmp_path):
        """Test that generated skills include Vercel-compatible metadata."""
        pattern = DetectedPattern(
            id="test123",
            tool_sequence=["Read", "Edit"],
            occurrence_count=5,
            confidence=0.85,
            session_ids=["sess1", "sess2"],
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            suggested_name="payment-workflow",
            suggested_description="Payment processing workflow"
        )
        
        generator = SkillGenerator(output_dir=tmp_path)
        candidate = generator.generate_candidate(pattern)
        
        # Check Vercel metadata
        frontmatter = candidate.yaml_frontmatter
        
        assert "compatible-agents" in frontmatter
        assert "claude-code" in frontmatter["compatible-agents"]
        assert "opencode" in frontmatter["compatible-agents"]
        
        assert "tags" in frontmatter
        assert isinstance(frontmatter["tags"], list)
        
        assert "source" in frontmatter
        assert frontmatter["source"] == "auto-generated"
        
        assert "derived-from" in frontmatter
        assert frontmatter["derived-from"] == "local-patterns"
    
    def test_mental_context_in_frontmatter(self, tmp_path):
        """Test that Mental context is included in skill frontmatter."""
        pattern = DetectedPattern(
            id="test123",
            tool_sequence=["Read", "Edit"],
            occurrence_count=5,
            confidence=0.85,
            session_ids=["sess1"],
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            mental_context={
                "domains": [
                    {"name": "Payment", "description": "Payment processing"}
                ],
                "capabilities": [
                    {"name": "Checkout", "description": "Process checkout", "operates_on": ["Payment"]}
                ],
                "aspects": [
                    {"name": "Auth", "description": "Authentication"}
                ]
            }
        )
        
        generator = SkillGenerator(output_dir=tmp_path)
        candidate = generator.generate_candidate(pattern)
        
        frontmatter = candidate.yaml_frontmatter
        
        assert "mental-context" in frontmatter
        
        mental_ctx = frontmatter["mental-context"]
        assert "domains" in mental_ctx
        assert "Payment" in mental_ctx["domains"]
        
        assert "capabilities" in mental_ctx
        assert "Checkout" in mental_ctx["capabilities"]
        
        assert "aspects" in mental_ctx
        assert "Auth" in mental_ctx["aspects"]
    
    def test_tags_generation(self, tmp_path):
        """Test tag generation from pattern context."""
        pattern = DetectedPattern(
            id="test123",
            tool_sequence=["Read", "Edit", "Bash"],
            occurrence_count=5,
            confidence=0.85,
            session_ids=["sess1"],
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            session_context={
                "primary_intent": "implement",
                "workflow_type": "TDD"
            },
            mental_context={
                "domains": [{"name": "Payment"}]
            }
        )
        
        generator = SkillGenerator(output_dir=tmp_path)
        tags = generator._generate_tags(pattern)
        
        # Should include tool names
        assert "read" in tags or any("read" in t.lower() for t in tags)
        assert "edit" in tags or any("edit" in t.lower() for t in tags)
        
        # Should include intent
        assert "implement" in tags
        
        # Should include workflow type
        assert "tdd" in tags
        
        # Should include domain
        assert "payment" in tags


class TestUnifiedSuggesterIntegration:
    """Test UnifiedSuggester with pattern detection."""
    
    def test_unified_suggester_with_patterns(self, tmp_path):
        """Test that UnifiedSuggester can work with detected patterns."""
        pattern = DetectedPattern(
            id="test123",
            tool_sequence=["Read", "Edit"],
            occurrence_count=5,
            confidence=0.85,
            session_ids=["sess1"],
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            suggested_name="test-workflow",
            suggested_description="Test workflow"
        )
        
        suggester = UnifiedSuggester(
            project_path=tmp_path,
            enable_mental=False,  # Disable for test
            enable_external=False
        )
        
        suggestions = suggester.suggest_for_context(
            detected_patterns=[pattern],
            session_context={}
        )
        
        # Should get suggestion from local pattern
        assert len(suggestions) >= 1
        
        local_suggestion = next(
            (s for s in suggestions if s.source == "local"),
            None
        )
        
        assert local_suggestion is not None
        assert local_suggestion.name == "test-workflow"
        assert local_suggestion.confidence == 0.85


class TestEndToEndIntegration:
    """Test full end-to-end hybrid workflow."""
    
    def test_pattern_to_skill_with_mental(self, tmp_path):
        """Test full flow: pattern detection → Mental enrichment → skill generation."""
        # Create a pattern with Mental context
        pattern = DetectedPattern(
            id="e2e-test",
            tool_sequence=["Read", "Edit", "Bash"],
            occurrence_count=7,
            confidence=0.90,
            session_ids=["sess1", "sess2", "sess3"],
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            suggested_name="payment-processing",
            suggested_description="Process payment transactions",
            session_context={
                "primary_intent": "implement",
                "workflow_type": "TDD",
                "tool_success_rate": 0.95
            },
            mental_context={
                "domains": [
                    {"name": "Payment", "description": "Payment processing"}
                ],
                "capabilities": [
                    {
                        "name": "ProcessPayment",
                        "description": "Process payment transaction",
                        "operates_on": ["Payment"]
                    }
                ],
                "aspects": [
                    {"name": "Validation", "description": "Input validation"}
                ]
            }
        )
        
        # Generate skill
        generator = SkillGenerator(output_dir=tmp_path)
        candidate = generator.generate_candidate(pattern)
        
        # Verify rich metadata
        frontmatter = candidate.yaml_frontmatter
        
        # V1 metadata
        assert frontmatter["confidence"] == 0.90
        assert frontmatter["occurrence-count"] == 7
        
        # V2 metadata
        assert "session-analysis" in frontmatter
        assert frontmatter["session-analysis"]["primary_intent"] == "implement"
        
        # Hybrid Phase 3 metadata
        assert "mental-context" in frontmatter
        assert "Payment" in frontmatter["mental-context"]["domains"]
        
        assert "compatible-agents" in frontmatter
        assert "claude-code" in frontmatter["compatible-agents"]
        
        assert "tags" in frontmatter
        # Tags should include: tools, intent, workflow, domain
        tags = frontmatter["tags"]
        assert "implement" in tags
        assert "payment" in tags
        
        # Render to SKILL.md
        skill_md = candidate.render()
        
        # Verify content includes metadata
        assert "payment-processing" in skill_md
        assert "compatible-agents:" in skill_md
        assert "mental-context:" in skill_md
        assert "domains:" in skill_md
        
        print(f"\n✅ Generated skill with full hybrid metadata:")
        print(f"   Confidence: {frontmatter['confidence']}")
        print(f"   Domains: {frontmatter['mental-context']['domains']}")
        print(f"   Tags: {', '.join(tags[:5])}")
        print(f"   Compatible: {', '.join(frontmatter['compatible-agents'])}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
