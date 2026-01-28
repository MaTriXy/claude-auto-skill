"""
Telemetry subcommand - view skill usage telemetry and effectiveness reports.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.telemetry import TelemetryCollector


def telemetry_command(args):
    """Handle telemetry subcommands."""
    if args.telemetry_action == "report":
        _telemetry_report(args)
    elif args.telemetry_action == "events":
        _telemetry_events(args)
    else:
        _telemetry_report(args)


def _telemetry_report(args):
    """Show effectiveness report."""
    collector = TelemetryCollector()
    skill_name = getattr(args, "skill", None)
    reports = collector.get_effectiveness_report(skill_name=skill_name)

    if getattr(args, "json", False):
        print(json.dumps({
            "count": len(reports),
            "reports": [r.to_dict() for r in reports],
        }, indent=2))
        return

    print("\n📊 Skill Effectiveness Report\n")
    if not reports:
        print("  No telemetry data yet.")
        return

    for report in reports:
        print(f"  {report.skill_name}")
        print(f"    Uses: {report.total_uses}")
        print(f"    Success Rate: {report.success_rate:.0%}")
        if report.avg_duration_ms:
            print(f"    Avg Duration: {report.avg_duration_ms:.0f}ms")
        print(f"    Agents: {', '.join(report.agents_used)}")
        print()


def _telemetry_events(args):
    """Show raw telemetry events."""
    collector = TelemetryCollector()
    skill_name = getattr(args, "skill", None)
    limit = getattr(args, "limit", 20)
    events = collector.get_events(skill_name=skill_name, limit=limit)

    if getattr(args, "json", False):
        print(json.dumps({
            "count": len(events),
            "events": [e.to_dict() for e in events],
        }, indent=2))
        return

    print(f"\n📋 Telemetry Events (latest {len(events)})\n")
    if not events:
        print("  No events recorded yet.")
        return

    for event in events:
        outcome_icon = "✅" if event.outcome == "success" else "❌"
        dur = f" ({event.duration_ms}ms)" if event.duration_ms else ""
        print(f"  {outcome_icon} {event.skill_name} [{event.agent_id}]{dur}")
        print(f"     Session: {event.session_id[:12]}... | {event.timestamp}")
