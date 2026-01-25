#!/usr/bin/env python3
"""
List Skills Script

Lists all auto-generated skills in the registry.

Usage:
    python list_skills.py
    python list_skills.py --verbose
"""

import sys
from pathlib import Path

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent))
from skill_registry import load_registry, rebuild_registry


def format_skill_list(registry: dict, verbose: bool = False) -> str:
    """Format the skill list for display."""
    skills = registry.get('skills', [])

    if not skills:
        return "No auto-generated skills found.\n\nRun /auto-skill:review to create skills from detected patterns."

    lines = [
        "## Auto-Generated Skills Registry",
        "",
        f"Total: {registry.get('total_skills', 0)} skills, ~{registry.get('total_tokens', 0):,} tokens",
        f"Location: {registry.get('skills_dir', 'unknown')}",
        "",
    ]

    if verbose:
        lines.append("| Name | Confidence | Context | Tools | Tokens |")
        lines.append("|------|------------|---------|-------|--------|")

        for skill in skills:
            name = skill['name']
            conf = f"{skill.get('confidence', 0):.0%}"
            tokens = f"~{skill.get('token_estimate', 0):,}"

            # Context indicator
            if skill.get('context') == 'fork':
                agent = skill.get('agent', 'general')
                context = f"fork:{agent}"
            else:
                context = "inline"

            # Allowed tools (abbreviated)
            allowed = skill.get('allowed_tools', [])
            if allowed:
                tools = ', '.join(allowed[:3])
                if len(allowed) > 3:
                    tools += f" +{len(allowed)-3}"
            else:
                tools = "all"

            lines.append(f"| {name} | {conf} | {context} | {tools} | {tokens} |")
    else:
        for skill in skills:
            conf = skill.get('confidence', 0)
            summary = skill.get('summary', '')[:50]
            if len(skill.get('summary', '')) > 50:
                summary += "..."

            # Add execution context indicator
            context_badge = ""
            if skill.get('context') == 'fork':
                context_badge = " [fork]"

            lines.append(f"- **{skill['name']}** ({conf:.0%}){context_badge}")
            if summary:
                lines.append(f"  {summary}")

    lines.append("")
    lines.append("Commands:")
    lines.append("- Load: `python scripts/get_skill.py <name>`")
    lines.append("- Search: `python scripts/search_skills.py <query>`")
    lines.append("- Or use: `/auto-skill:load <name>`")

    return "\n".join(lines)


def main():
    """Main entry point."""
    args = sys.argv[1:]

    verbose = '--verbose' in args or '-v' in args
    rebuild = '--rebuild' in args

    if '--help' in args or '-h' in args:
        print("Usage: python list_skills.py [OPTIONS]")
        print("")
        print("List all auto-generated skills in the registry.")
        print("")
        print("Options:")
        print("  --verbose, -v   Show detailed table view")
        print("  --rebuild       Rebuild registry from disk")
        print("  --help, -h      Show this help")
        return

    # Load or rebuild registry
    if rebuild:
        registry = rebuild_registry()
    else:
        registry = load_registry()
        if not registry:
            registry = rebuild_registry()

    print(format_skill_list(registry, verbose))


if __name__ == "__main__":
    main()
