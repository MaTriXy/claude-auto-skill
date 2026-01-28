#!/usr/bin/env python3
"""
Unified CLI for Claude Auto-Skill.

Usage:
    auto-skill init              # Initialize auto-skill
    auto-skill discover          # Discover skills for current project
    auto-skill search QUERY      # Search external skills
    auto-skill stats             # Show adoption statistics
    auto-skill graduate          # Manage skill graduation
    auto-skill agents list       # List known agents
    auto-skill agents detect     # Detect installed agents
    auto-skill lock status       # Show lock file status
    auto-skill lock verify       # Verify skill integrity
    auto-skill lock list         # List locked skills
    auto-skill telemetry report  # Show effectiveness report
    auto-skill telemetry events  # Show raw events
    auto-skill version           # Show version
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def _get_version() -> str:
    """Get the package version."""
    try:
        from importlib.metadata import version
        return version("claude-auto-skill")
    except Exception:
        return "3.0.0"


def version_command(args):
    """Show version."""
    print(f"claude-auto-skill {_get_version()}")


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    # Shared arguments via parent parser
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="Output as JSON")

    parser = argparse.ArgumentParser(
        prog="auto-skill",
        description="Claude Auto-Skill - Automatically learn and generate skills",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init
    init_parser = subparsers.add_parser("init", parents=[common], help="Initialize auto-skill")
    init_parser.add_argument("--force", action="store_true", help="Force recreate config")

    # discover
    discover_parser = subparsers.add_parser("discover", parents=[common], help="Discover skills")
    discover_parser.add_argument("--project", help="Project path")
    discover_parser.add_argument("--no-mental", action="store_true")
    discover_parser.add_argument("--no-external", action="store_true")
    discover_parser.add_argument("--limit", type=int, default=10)

    # search
    search_parser = subparsers.add_parser("search", parents=[common], help="Search external skills")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", type=int, default=10)

    # stats
    stats_parser = subparsers.add_parser("stats", parents=[common], help="Show adoption statistics")
    stats_parser.add_argument("--project", help="Project path")

    # graduate
    graduate_parser = subparsers.add_parser("graduate", parents=[common], help="Manage skill graduation")
    graduate_parser.add_argument(
        "graduate_action", nargs="?", default="detect",
        choices=["detect", "auto", "stats", "history"],
    )
    graduate_parser.add_argument("--max", type=int, default=5)

    # agents
    agents_parser = subparsers.add_parser("agents", parents=[common], help="Manage agent configurations")
    agents_parser.add_argument(
        "agent_action", nargs="?", default="list",
        choices=["list", "detect"],
    )

    # lock
    lock_parser = subparsers.add_parser("lock", parents=[common], help="Manage skill lock file")
    lock_parser.add_argument(
        "lock_action", nargs="?", default="status",
        choices=["status", "verify", "list"],
    )

    # telemetry
    telemetry_parser = subparsers.add_parser("telemetry", parents=[common], help="View usage telemetry")
    telemetry_parser.add_argument(
        "telemetry_action", nargs="?", default="report",
        choices=["report", "events"],
    )
    telemetry_parser.add_argument("--skill", help="Filter to specific skill")
    telemetry_parser.add_argument("--limit", type=int, default=20)

    # version
    subparsers.add_parser("version", help="Show version")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "version":
        version_command(args)

    elif args.command == "init":
        from commands.init import init_command
        init_command(args)

    elif args.command == "discover":
        from commands.discover import discover_command
        discover_command(args)

    elif args.command == "search":
        # Adapt args for the existing search command
        from commands.discover import search_command
        args.search = args.query
        search_command(args)

    elif args.command == "stats":
        from commands.discover import stats_command
        stats_command(args)

    elif args.command == "graduate":
        from core.graduation_manager import main as graduate_main
        # Forward to graduation manager CLI
        sys.argv = ["graduate", args.graduate_action]
        if args.graduate_action == "auto":
            sys.argv.append(str(args.max))
        graduate_main()

    elif args.command == "agents":
        from commands.agents import agents_command
        agents_command(args)

    elif args.command == "lock":
        from commands.lock import lock_command
        lock_command(args)

    elif args.command == "telemetry":
        from commands.telemetry_cmd import telemetry_command
        telemetry_command(args)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
