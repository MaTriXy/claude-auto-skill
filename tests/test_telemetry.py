"""Tests for the telemetry module."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.telemetry import (
    TelemetryCollector, TelemetryEvent, EffectivenessReport,
    track, is_telemetry_disabled, TOOL_ID, TELEMETRY_ENDPOINT,
)


class TestTelemetryCollector:
    """Tests for TelemetryCollector."""

    @pytest.fixture
    def collector(self, tmp_path):
        return TelemetryCollector(db_path=tmp_path / "telemetry.db")

    def test_record_event(self, collector):
        event = collector.record_event(
            skill_id="s1",
            skill_name="my-skill",
            session_id="sess-1",
            outcome="success",
            agent_id="claude-code",
            duration_ms=150,
        )
        assert event.id
        assert event.skill_name == "my-skill"
        assert event.outcome == "success"
        assert event.duration_ms == 150

    def test_get_events(self, collector):
        collector.record_event("s1", "skill-a", "sess-1", "success")
        collector.record_event("s2", "skill-b", "sess-1", "failure")

        events = collector.get_events()
        assert len(events) == 2

    def test_get_events_filtered(self, collector):
        collector.record_event("s1", "skill-a", "sess-1", "success")
        collector.record_event("s2", "skill-b", "sess-1", "failure")

        events = collector.get_events(skill_name="skill-a")
        assert len(events) == 1
        assert events[0].skill_name == "skill-a"

    def test_get_events_limit(self, collector):
        for i in range(10):
            collector.record_event(f"s{i}", f"skill-{i}", "sess", "success")

        events = collector.get_events(limit=3)
        assert len(events) == 3

    def test_effectiveness_report(self, collector):
        # Record mixed outcomes for a skill
        collector.record_event("s1", "my-skill", "sess-1", "success", duration_ms=100)
        collector.record_event("s1", "my-skill", "sess-2", "success", duration_ms=200)
        collector.record_event("s1", "my-skill", "sess-3", "failure", duration_ms=50)

        reports = collector.get_effectiveness_report()
        assert len(reports) == 1

        report = reports[0]
        assert report.skill_name == "my-skill"
        assert report.total_uses == 3
        assert report.success_count == 2
        assert report.failure_count == 1
        assert abs(report.success_rate - 2/3) < 0.01
        assert report.avg_duration_ms is not None

    def test_effectiveness_report_filtered(self, collector):
        collector.record_event("s1", "skill-a", "sess", "success")
        collector.record_event("s2", "skill-b", "sess", "success")

        reports = collector.get_effectiveness_report(skill_name="skill-a")
        assert len(reports) == 1
        assert reports[0].skill_name == "skill-a"

    def test_effectiveness_report_multi_agent(self, collector):
        collector.record_event("s1", "my-skill", "sess-1", "success", agent_id="claude-code")
        collector.record_event("s1", "my-skill", "sess-2", "success", agent_id="codex")

        reports = collector.get_effectiveness_report()
        assert set(reports[0].agents_used) == {"claude-code", "codex"}

    def test_recording_performance(self, collector):
        """Recording should be fast (no expensive operations)."""
        import time
        start = time.time()
        for i in range(100):
            collector.record_event(f"s{i}", f"skill-{i}", "sess", "success")
        elapsed = time.time() - start
        # 100 inserts should complete in under 5 seconds
        assert elapsed < 5.0

    def test_empty_report(self, collector):
        reports = collector.get_effectiveness_report()
        assert reports == []


class TestTelemetryEvent:
    """Tests for TelemetryEvent dataclass."""

    def test_to_dict(self):
        event = TelemetryEvent(
            id="1", skill_id="s1", skill_name="test",
            session_id="sess", agent_id="claude",
            duration_ms=100, outcome="success",
            timestamp="2024-01-01T00:00:00"
        )
        d = event.to_dict()
        assert d["skill_name"] == "test"
        assert d["outcome"] == "success"
        assert d["duration_ms"] == 100


class TestEffectivenessReport:
    """Tests for EffectivenessReport dataclass."""

    def test_to_dict(self):
        report = EffectivenessReport(
            skill_name="test", total_uses=10,
            success_count=8, failure_count=2,
            success_rate=0.8, avg_duration_ms=150.5,
            agents_used=["claude-code"], last_used="2024-01-01"
        )
        d = report.to_dict()
        assert d["success_rate"] == 0.8
        assert d["avg_duration_ms"] == 150  # rounded


class TestAnonymousTelemetry:
    """Tests for the anonymous telemetry module (fire-and-forget remote reporting)."""

    def test_opt_out_tool_specific(self):
        """AUTO_SKILL_NO_TELEMETRY=1 disables telemetry."""
        with patch.dict(os.environ, {"AUTO_SKILL_NO_TELEMETRY": "1"}, clear=False):
            assert is_telemetry_disabled() is True

    def test_opt_out_do_not_track(self):
        """DO_NOT_TRACK=1 disables telemetry (universal standard)."""
        with patch.dict(os.environ, {"DO_NOT_TRACK": "1"}, clear=False):
            assert is_telemetry_disabled() is True

    def test_opt_out_ci_github_actions(self):
        """CI environments auto-disable telemetry."""
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=False):
            assert is_telemetry_disabled() is True

    def test_opt_out_ci_generic(self):
        """Generic CI=true disables telemetry."""
        with patch.dict(os.environ, {"CI": "true"}, clear=False):
            assert is_telemetry_disabled() is True

    def test_enabled_by_default(self):
        """Telemetry is enabled when no opt-out env vars are set."""
        clean_env = {k: v for k, v in os.environ.items()
                     if k not in ("AUTO_SKILL_NO_TELEMETRY", "DO_NOT_TRACK",
                                  "CI", "GITHUB_ACTIONS", "GITLAB_CI", "CIRCLECI",
                                  "TRAVIS", "BUILDKITE", "JENKINS_URL")}
        with patch.dict(os.environ, clean_env, clear=True):
            assert is_telemetry_disabled() is False

    @patch("core.telemetry.threading.Thread")
    def test_track_fires_daemon_thread(self, mock_thread_cls):
        """track() fires a daemon background thread."""
        mock_thread = MagicMock()
        mock_thread_cls.return_value = mock_thread

        clean_env = {k: v for k, v in os.environ.items()
                     if k not in ("AUTO_SKILL_NO_TELEMETRY", "DO_NOT_TRACK",
                                  "CI", "GITHUB_ACTIONS", "GITLAB_CI", "CIRCLECI",
                                  "TRAVIS", "BUILDKITE", "JENKINS_URL")}
        with patch.dict(os.environ, clean_env, clear=True):
            track("test_event", {"n": 5})

        mock_thread_cls.assert_called_once()
        _, kwargs = mock_thread_cls.call_args
        assert kwargs["daemon"] is True
        mock_thread.start.assert_called_once()

    @patch("core.telemetry.threading.Thread")
    def test_track_skipped_when_disabled(self, mock_thread_cls):
        """track() does nothing when telemetry is disabled."""
        with patch.dict(os.environ, {"DO_NOT_TRACK": "1"}, clear=False):
            track("test_event")

        mock_thread_cls.assert_not_called()

    @patch("core.telemetry.threading.Thread")
    def test_track_includes_tool_id(self, mock_thread_cls):
        """track() includes the tool identifier in the payload."""
        mock_thread = MagicMock()
        mock_thread_cls.return_value = mock_thread

        clean_env = {k: v for k, v in os.environ.items()
                     if k not in ("AUTO_SKILL_NO_TELEMETRY", "DO_NOT_TRACK",
                                  "CI", "GITHUB_ACTIONS", "GITLAB_CI", "CIRCLECI",
                                  "TRAVIS", "BUILDKITE", "JENKINS_URL")}
        with patch.dict(os.environ, clean_env, clear=True):
            track("skill_used", {"outcome": "success"})

        # The URL passed to the thread target should contain our tool ID
        args, kwargs = mock_thread_cls.call_args
        url = kwargs["args"][0]
        assert f"t={TOOL_ID}" in url
        assert "e=skill_used" in url
        assert "outcome=success" in url

    @patch("core.telemetry.track")
    def test_record_event_fires_track(self, mock_track, tmp_path):
        """TelemetryCollector.record_event() also fires anonymous telemetry."""
        collector = TelemetryCollector(db_path=tmp_path / "telemetry.db")
        collector.record_event("s1", "my-skill", "sess", "success", duration_ms=100)

        mock_track.assert_called_once_with("skill_used", {
            "outcome": "success",
            "agent": "unknown",
            "ms": 100,
        })

    def test_track_silent_failure(self):
        """track() never raises, even with broken internals."""
        clean_env = {k: v for k, v in os.environ.items()
                     if k not in ("AUTO_SKILL_NO_TELEMETRY", "DO_NOT_TRACK",
                                  "CI", "GITHUB_ACTIONS", "GITLAB_CI", "CIRCLECI",
                                  "TRAVIS", "BUILDKITE", "JENKINS_URL")}
        with patch.dict(os.environ, clean_env, clear=True):
            with patch("core.telemetry.urlencode", side_effect=Exception("boom")):
                # Should not raise
                track("broken_event")

    def test_no_pii_in_payload(self):
        """Verify the anonymous payload contains no PII fields."""
        # The track() function only sends: t, e, v, py, os, and caller-provided data.
        # record_event sends: outcome, agent, ms — none of which are PII.
        # Verify by checking no session_id, skill_id, or paths are sent.
        with patch("core.telemetry.threading.Thread") as mock_cls:
            mock_cls.return_value = MagicMock()
            clean_env = {k: v for k, v in os.environ.items()
                         if k not in ("AUTO_SKILL_NO_TELEMETRY", "DO_NOT_TRACK",
                                      "CI", "GITHUB_ACTIONS", "GITLAB_CI", "CIRCLECI",
                                      "TRAVIS", "BUILDKITE", "JENKINS_URL")}
            with patch.dict(os.environ, clean_env, clear=True):
                track("skill_used", {"outcome": "success", "ms": 50})

            url = mock_cls.call_args[1]["args"][0]
            assert "session" not in url.lower()
            assert "skill_id" not in url
            assert "/home" not in url
            assert "/Users" not in url
