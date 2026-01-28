"""Tests for the well-known provider."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.providers.wellknown_provider import WellKnownProvider
from core.providers.base import SkillProvider


class TestWellKnownProvider:
    """Tests for WellKnownProvider."""

    def test_implements_protocol(self):
        provider = WellKnownProvider(domains=["example.com"])
        assert isinstance(provider, SkillProvider)

    def test_is_available_with_domains(self):
        provider = WellKnownProvider(domains=["example.com"])
        assert provider.is_available() is True

    def test_is_not_available_without_domains(self):
        provider = WellKnownProvider(domains=[])
        assert provider.is_available() is False

    def test_name_and_source_id(self):
        provider = WellKnownProvider()
        assert provider.name == "Well-Known Discovery"
        assert provider.source_id == "wellknown"

    @patch("core.providers.wellknown_provider.urllib.request.urlopen")
    def test_search_valid_manifest(self, mock_urlopen):
        manifest = {
            "skills": [
                {
                    "id": "s1",
                    "name": "auth-flow",
                    "description": "Authentication workflow",
                    "tags": ["auth"],
                    "author": "test-author",
                },
                {
                    "id": "s2",
                    "name": "payment-handler",
                    "description": "Payment processing",
                    "tags": ["payment"],
                },
            ]
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(manifest).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        provider = WellKnownProvider(domains=["example.com"])
        results = provider.search("auth")

        assert len(results) == 1
        assert results[0].name == "auth-flow"
        assert results[0].source == "wellknown"

    @patch("core.providers.wellknown_provider.urllib.request.urlopen")
    def test_search_empty_query_returns_all(self, mock_urlopen):
        manifest = {
            "skills": [
                {"id": "s1", "name": "skill-1", "description": "First"},
                {"id": "s2", "name": "skill-2", "description": "Second"},
            ]
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(manifest).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        provider = WellKnownProvider(domains=["example.com"])
        results = provider.search("")

        assert len(results) == 2

    @patch("core.providers.wellknown_provider.urllib.request.urlopen")
    def test_caching(self, mock_urlopen):
        manifest = {"skills": [{"id": "s1", "name": "cached", "description": "Test"}]}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(manifest).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        provider = WellKnownProvider(domains=["example.com"], cache_ttl=3600)

        # First call fetches
        provider.search("")
        assert mock_urlopen.call_count == 1

        # Second call uses cache
        provider.search("")
        assert mock_urlopen.call_count == 1  # Not called again

    @patch("core.providers.wellknown_provider.urllib.request.urlopen")
    def test_graceful_failure(self, mock_urlopen):
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("Connection refused")

        provider = WellKnownProvider(domains=["nonexistent.invalid"])
        results = provider.search("test")

        assert results == []

    @patch("core.providers.wellknown_provider.urllib.request.urlopen")
    def test_invalid_manifest_structure(self, mock_urlopen):
        # Not a JSON object
        mock_response = MagicMock()
        mock_response.read.return_value = b'"just a string"'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        provider = WellKnownProvider(domains=["example.com"])
        results = provider.search("test")

        assert results == []

    @patch("core.providers.wellknown_provider.urllib.request.urlopen")
    def test_get_skill_details(self, mock_urlopen):
        manifest = {
            "skills": [
                {"id": "s1", "name": "target-skill", "description": "Found it"},
            ]
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(manifest).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        provider = WellKnownProvider(domains=["example.com"])
        result = provider.get_skill_details("s1")

        assert result is not None
        assert result.name == "target-skill"

    @patch("core.providers.wellknown_provider.urllib.request.urlopen")
    def test_get_skill_details_not_found(self, mock_urlopen):
        manifest = {"skills": []}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(manifest).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        provider = WellKnownProvider(domains=["example.com"])
        result = provider.get_skill_details("nonexistent")

        assert result is None
