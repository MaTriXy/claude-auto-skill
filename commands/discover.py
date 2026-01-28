#!/usr/bin/env python3
"""
Skill Discovery Command - Find and explore skills from all sources.

Usage:
    python -m commands.discover                    # Discover skills for current project
    python -m commands.discover --search "payment" # Search external skills
    python -m commands.discover --stats            # Show adoption stats
    python -m commands.discover --domain Payment   # Suggest for domain
    python -m commands.discover --candidates       # Show graduation candidates
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.unified_suggester import UnifiedSuggester
from core.skillssh_client import SkillsShClient
from core.providers import ProviderManager, SkillsShProvider, LocalProvider


def format_confidence_bar(confidence: float, width: int = 10) -> str:
    """Format confidence as a progress bar."""
    filled = int(confidence * width)
    return "█" * filled + "░" * (width - filled)


def format_source_emoji(source: str) -> str:
    """Get emoji for skill source."""
    emoji_map = {
        "local": "🏠",
        "external": "🌐",
        "mental-hint": "🧠"
    }
    return emoji_map.get(source, "❓")


def output_json(data: dict):
    """Output data as JSON."""
    print(json.dumps(data, indent=2, default=str))


def discover_command(args):
    """Discover skills based on current project context."""
    project_path = Path(args.project) if args.project else Path.cwd()

    suggester = UnifiedSuggester(
        project_path=project_path,
        enable_mental=not args.no_mental,
        enable_external=not args.no_external
    )

    # Get suggestions (in real use, would integrate with current session)
    suggestions = suggester.suggest_for_context(
        detected_patterns=[],  # Would come from pattern detector
        session_context={},    # Would come from session analyzer
        file_paths=[]          # Would come from current work
    )

    # JSON output
    if args.json:
        output_json({
            "project_path": str(project_path),
            "count": len(suggestions),
            "suggestions": [s.to_dict() for s in suggestions]
        })
        return

    # Human-readable output
    print(f"\n🔍 Discovering skills for: {project_path}\n")

    if not suggestions:
        print("ℹ️  No suggestions found. Try:")
        print("  • Working on some files first (to activate Mental context)")
        print("  • Using --search to find external skills")
        print("  • Enabling Mental model: mental add domain YourDomain")
        return

    print(f"Found {len(suggestions)} skill suggestions:\n")

    for i, suggestion in enumerate(suggestions, 1):
        confidence_bar = format_confidence_bar(suggestion.confidence)
        source_emoji = format_source_emoji(suggestion.source)

        print(f"{i}. {source_emoji} {suggestion.name}")
        print(f"   {suggestion.description}")
        print(f"   Confidence: [{confidence_bar}] {suggestion.confidence:.0%}")
        print(f"   Source: {suggestion.source}")

        # Show adoption stats if available
        if suggestion.adoption:
            adoption = suggestion.adoption
            print(f"   Usage: {adoption.usage_count} times "
                  f"({adoption.success_count} successes, {adoption.failure_count} failures)")
            print(f"   Success Rate: {adoption.success_rate:.0%}")

        # Show Mental context if available
        if suggestion.mental_context:
            context = suggestion.mental_context
            if "domains" in context:
                print(f"   Domains: {', '.join(context['domains'])}")
            if "capability" in context:
                print(f"   Capability: {context['capability']}")

        # Show external metadata if available
        if suggestion.external_metadata:
            meta = suggestion.external_metadata
            print(f"   Author: {meta.get('author', 'unknown')}")
            print(f"   Installs: {meta.get('install_count', 0)}")

        print()


def search_command(args):
    """Search for external skills."""
    client = SkillsShClient()

    # Check if API is available
    if not client.is_available():
        if args.json:
            output_json({"error": "Skills.sh API is not available", "skills": []})
        else:
            print("❌ Skills.sh API is not available. Check your internet connection.")
        return

    skills = client.search(args.search, limit=args.limit)

    # JSON output
    if args.json:
        output_json({
            "query": args.search,
            "count": len(skills),
            "skills": [s.to_dict() for s in skills]
        })
        return

    # Human-readable output
    print(f"\n🌐 Searching Skills.sh for: '{args.search}'\n")

    if not skills:
        print(f"No skills found for query: {args.search}")
        return

    print(f"Found {len(skills)} skills:\n")

    for i, skill in enumerate(skills, 1):
        print(f"{i}. {skill.name}")
        print(f"   {skill.description}")
        print(f"   Author: {skill.author}")
        print(f"   Installs: {skill.install_count}")
        if skill.tags:
            print(f"   Tags: {', '.join(skill.tags)}")
        if skill.source_url:
            print(f"   URL: {skill.source_url}")
        print()


def stats_command(args):
    """Show adoption statistics."""
    project_path = Path(args.project) if args.project else Path.cwd()

    suggester = UnifiedSuggester(project_path=project_path)
    adoptions = suggester.get_adoption_stats(min_confidence=0.0)

    # JSON output
    if args.json:
        output_json({
            "project_path": str(project_path),
            "count": len(adoptions),
            "adoptions": [a.to_dict() for a in adoptions]
        })
        return

    # Human-readable output
    print(f"\n📊 Adoption Statistics\n")

    if not adoptions:
        print("ℹ️  No skills have been adopted yet.")
        print("\nTo start tracking:")
        print("  1. Use skills from discovery")
        print("  2. System will automatically track usage")
        print("  3. Confidence evolves based on success rate")
        return

    print(f"Tracking {len(adoptions)} skills:\n")

    for adoption in adoptions:
        confidence_bar = format_confidence_bar(adoption.current_confidence)
        source_emoji = format_source_emoji(adoption.source)

        status = ""
        if adoption.graduated_to_local:
            status = " ⭐ (graduated)"
        elif adoption.source == "external" and adoption.current_confidence >= 0.75:
            status = " 🔥 (proven)"

        print(f"{source_emoji} {adoption.skill_name}{status}")
        print(f"   Confidence: [{confidence_bar}] {adoption.current_confidence:.0%}")
        print(f"   Usage: {adoption.usage_count} times "
              f"({adoption.success_count} successes, {adoption.failure_count} failures)")
        print(f"   Success Rate: {adoption.success_rate:.0%}")
        print(f"   First Used: {adoption.first_used.strftime('%Y-%m-%d')}")
        print(f"   Last Used: {adoption.last_used.strftime('%Y-%m-%d')}")
        print()


def domain_command(args):
    """Suggest skills for a specific domain."""
    project_path = Path(args.project) if args.project else Path.cwd()

    suggester = UnifiedSuggester(
        project_path=project_path,
        enable_mental=True,
        enable_external=False
    )

    suggestions = suggester.suggest_for_domain(args.domain, limit=args.limit)

    # JSON output
    if args.json:
        output_json({
            "domain": args.domain,
            "project_path": str(project_path),
            "count": len(suggestions),
            "suggestions": [s.to_dict() for s in suggestions]
        })
        return

    # Human-readable output
    print(f"\n🧠 Skills for domain: {args.domain}\n")

    if not suggestions:
        print(f"ℹ️  No suggestions for domain '{args.domain}'.")
        print("\nTry:")
        print(f"  mental add domain {args.domain} --desc 'Your description'")
        print(f"  mental add capability YourAction --operates-on {args.domain}")
        return

    print(f"Found {len(suggestions)} suggestions:\n")

    for i, suggestion in enumerate(suggestions, 1):
        confidence_bar = format_confidence_bar(suggestion.confidence)

        print(f"{i}. {suggestion.name}")
        print(f"   {suggestion.description}")
        print(f"   Confidence: [{confidence_bar}] {suggestion.confidence:.0%}")

        if suggestion.mental_context:
            context = suggestion.mental_context
            if "capability" in context:
                print(f"   Capability: {context['capability']}")

        print()


def candidates_command(args):
    """Show skills ready for graduation."""
    project_path = Path(args.project) if args.project else Path.cwd()

    suggester = UnifiedSuggester(project_path=project_path)
    candidates = suggester.get_graduation_candidates()

    # JSON output
    if args.json:
        output_json({
            "project_path": str(project_path),
            "count": len(candidates),
            "candidates": [c.to_dict() for c in candidates]
        })
        return

    # Human-readable output
    print(f"\n⭐ Graduation Candidates\n")

    if not candidates:
        print("ℹ️  No skills ready for graduation yet.")
        print("\nGraduation criteria:")
        print("  • Confidence ≥ 85%")
        print("  • Used at least 5 times")
        print("  • Success rate ≥ 80%")
        return

    print(f"Found {len(candidates)} skills ready to graduate:\n")

    for adoption in candidates:
        confidence_bar = format_confidence_bar(adoption.current_confidence)

        print(f"🌐 {adoption.skill_name}")
        print(f"   Confidence: [{confidence_bar}] {adoption.current_confidence:.0%}")
        print(f"   Usage: {adoption.usage_count} times "
              f"({adoption.success_count} successes, {adoption.failure_count} failures)")
        print(f"   Success Rate: {adoption.success_rate:.0%}")
        print(f"   Ready to graduate to local skill! ⭐")
        print()


def effectiveness_command(args):
    """Show skill effectiveness report from telemetry."""
    from core.telemetry import TelemetryCollector

    collector = TelemetryCollector()
    reports = collector.get_effectiveness_report()

    if args.json:
        output_json({
            "count": len(reports),
            "reports": [r.to_dict() for r in reports]
        })
        return

    print("\n📊 Skill Effectiveness Report\n")

    if not reports:
        print("No telemetry data yet. Use skills to start collecting data.")
        return

    for report in reports:
        bar = format_confidence_bar(report.success_rate)
        print(f"  {report.skill_name}")
        print(f"    Uses: {report.total_uses} | Success: [{bar}] {report.success_rate:.0%}")
        if report.avg_duration_ms:
            print(f"    Avg Duration: {report.avg_duration_ms:.0f}ms")
        print(f"    Agents: {', '.join(report.agents_used)}")
        print(f"    Last Used: {report.last_used}")
        print()


def wellknown_command(args):
    """Discover skills from well-known endpoints."""
    from core.providers.wellknown_provider import WellKnownProvider

    domains = args.wellknown if args.wellknown else []

    if not domains:
        if args.json:
            output_json({"error": "No domains specified", "skills": []})
        else:
            print("No domains specified. Usage: --wellknown example.com skills.dev")
        return

    provider = WellKnownProvider(domains=domains)
    results = provider.search("", limit=args.limit)

    if args.json:
        output_json({
            "domains": domains,
            "count": len(results),
            "skills": [r.to_dict() for r in results]
        })
        return

    print(f"\n🌐 Well-Known Discovery ({len(domains)} domains)\n")

    if not results:
        print("No skills found from specified domains.")
        return

    print(f"Found {len(results)} skills:\n")
    for i, skill in enumerate(results, 1):
        print(f"{i}. {skill.name}")
        print(f"   {skill.description}")
        if skill.author:
            print(f"   Author: {skill.author}")
        if skill.tags:
            print(f"   Tags: {', '.join(skill.tags)}")
        print(f"   Source: {skill.metadata.get('domain', 'unknown') if skill.metadata else 'unknown'}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Discover skills from Mental, Skills.sh, and local patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--project", help="Project path (default: current directory)")
    parser.add_argument("--no-mental", action="store_true", help="Disable Mental integration")
    parser.add_argument("--no-external", action="store_true", help="Disable Skills.sh")

    # Commands
    parser.add_argument("--search", help="Search Skills.sh for skills")
    parser.add_argument("--stats", action="store_true", help="Show adoption statistics")
    parser.add_argument("--domain", help="Suggest skills for a Mental domain")
    parser.add_argument("--candidates", action="store_true", help="Show graduation candidates")
    parser.add_argument(
        "--wellknown", nargs="*", metavar="DOMAIN",
        help="Discover skills from well-known endpoints (RFC 8615)"
    )
    parser.add_argument(
        "--effectiveness", action="store_true",
        help="Show skill effectiveness report from telemetry"
    )

    # Output options
    parser.add_argument("--json", action="store_true", help="Output as JSON (for scripting)")
    parser.add_argument("--limit", type=int, default=10, help="Limit number of results")

    args = parser.parse_args()

    # Route to appropriate command
    if args.search:
        search_command(args)
    elif args.stats:
        stats_command(args)
    elif args.domain:
        domain_command(args)
    elif args.candidates:
        candidates_command(args)
    elif args.wellknown is not None:
        wellknown_command(args)
    elif args.effectiveness:
        effectiveness_command(args)
    else:
        discover_command(args)


if __name__ == "__main__":
    main()
