"""Tests for the providers module."""

import pytest
from pathlib import Path
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.providers.base import SkillProvider, SkillSearchResult
from core.providers.skillssh_provider import SkillsShProvider


class MockProvider:
    """A mock provider for testing the SkillProvider protocol."""

    def __init__(self, skills: list[SkillSearchResult] = None, available: bool = True):
        self._skills = skills or []
        self._available = available

    @property
    def name(self) -> str:
        return "Mock Provider"

    @property
    def source_id(self) -> str:
        return "mock"

    def search(self, query: str, limit: int = 10) -> list[SkillSearchResult]:
        return [s for s in self._skills if query.lower() in s.name.lower()][:limit]

    def get_skill_details(self, skill_id: str) -> Optional[SkillSearchResult]:
        for s in self._skills:
            if s.id == skill_id:
                return s
        return None

    def is_available(self) -> bool:
        return self._available


class TestSkillProviderProtocol:
    """Test that MockProvider satisfies the SkillProvider protocol."""

    def test_mock_implements_protocol(self):
        provider = MockProvider()
        assert isinstance(provider, SkillProvider)

    def test_skillssh_provider_implements_protocol(self):
        # SkillsShProvider should also implement the protocol
        provider = SkillsShProvider.__new__(SkillsShProvider)
        assert isinstance(provider, SkillProvider)


class TestMockProvider:
    """Tests for MockProvider functionality."""

    @pytest.fixture
    def skills(self):
        return [
            SkillSearchResult(
                id="1", name="payment-handler", description="Handles payments",
                source="mock", tags=["payment"]
            ),
            SkillSearchResult(
                id="2", name="auth-flow", description="Authentication workflow",
                source="mock", tags=["auth"]
            ),
        ]

    def test_search_returns_matches(self, skills):
        provider = MockProvider(skills=skills)
        results = provider.search("payment")
        assert len(results) == 1
        assert results[0].name == "payment-handler"

    def test_search_no_matches(self, skills):
        provider = MockProvider(skills=skills)
        results = provider.search("nonexistent")
        assert len(results) == 0

    def test_search_with_limit(self, skills):
        provider = MockProvider(skills=skills)
        results = provider.search("", limit=1)  # empty query matches nothing via our mock
        assert len(results) <= 1

    def test_get_skill_details(self, skills):
        provider = MockProvider(skills=skills)
        result = provider.get_skill_details("1")
        assert result is not None
        assert result.name == "payment-handler"

    def test_get_skill_details_not_found(self, skills):
        provider = MockProvider(skills=skills)
        result = provider.get_skill_details("999")
        assert result is None

    def test_is_available(self):
        assert MockProvider(available=True).is_available() is True
        assert MockProvider(available=False).is_available() is False


class TestSkillSearchResult:
    """Tests for SkillSearchResult dataclass."""

    def test_to_dict(self):
        result = SkillSearchResult(
            id="1", name="test", description="A test skill",
            source="mock", confidence=0.8, author="user",
            tags=["tag1"]
        )
        d = result.to_dict()
        assert d["id"] == "1"
        assert d["name"] == "test"
        assert d["source"] == "mock"
        assert d["confidence"] == 0.8

    def test_defaults(self):
        result = SkillSearchResult(
            id="1", name="test", description="desc", source="mock"
        )
        assert result.confidence == 0.5
        assert result.tags == []
        assert result.author == ""
