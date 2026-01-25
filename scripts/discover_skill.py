#!/usr/bin/env python3
"""
Discover Skill Script

Searches for skills matching a query and outputs the best match
if it meets the confidence threshold. This is the script Claude
uses to proactively discover and offer skills.

Usage:
    python discover_skill.py "search and fix bugs"
    python discover_skill.py "search and fix bugs" --auto-load
    python discover_skill.py "search and fix bugs" --threshold 0.7
"""

import sys
from pathlib import Path

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent))
from skill_registry import load_registry, rebuild_registry
from search_skills import search_skills, tokenize
from get_skill import find_skill, load_skill_content, format_skill_output


def discover_skill(
    query: str,
    min_score: float = 3.0,
    min_confidence: float = 0.6,
    auto_load: bool = False
) -> dict:
    """
    Discover a skill matching the query.

    Args:
        query: User's intent/task description
        min_score: Minimum search score to consider a match
        min_confidence: Minimum skill confidence to consider
        auto_load: If True, output full skill content; if False, just metadata

    Returns:
        Dict with discovery results
    """
    # Load registry
    registry = load_registry()
    if not registry:
        registry = rebuild_registry()

    # Search for matches
    results = search_skills(registry, query, top_n=3)

    if not results:
        return {
            'found': False,
            'message': f"No skills found matching '{query}'."
        }

    # Check best match
    best_skill, best_score = results[0]

    # Check thresholds
    if best_score < min_score:
        return {
            'found': False,
            'message': f"Found skills but none matched well enough (best score: {best_score:.1f}, need: {min_score})."
        }

    if best_skill.get('confidence', 0) < min_confidence:
        return {
            'found': False,
            'message': f"Found a match but confidence too low ({best_skill.get('confidence', 0):.0%}, need: {min_confidence:.0%})."
        }

    # Found a good match
    result = {
        'found': True,
        'skill': best_skill,
        'score': best_score,
        'alternatives': [(s['name'], score) for s, score in results[1:3] if score > min_score * 0.7]
    }

    if auto_load:
        # Load and include full content
        content = load_skill_content(best_skill)
        if content:
            result['content'] = format_skill_output(best_skill, content)

    return result


def format_discovery_output(result: dict, show_alternatives: bool = True) -> str:
    """Format discovery results for Claude to present to user."""
    if not result['found']:
        return result['message']

    skill = result['skill']
    score = result['score']

    lines = []
    lines.append("## Skill Discovery")
    lines.append("")
    lines.append(f"I found an auto-generated skill that matches your task:")
    lines.append("")
    lines.append(f"**{skill['name']}** (confidence: {skill.get('confidence', 0):.0%})")
    lines.append(f"> {skill.get('description', skill.get('summary', 'No description'))}")
    lines.append("")

    # Show execution context
    if skill.get('context') == 'fork':
        lines.append(f"- Runs in: Isolated subagent ({skill.get('agent', 'general-purpose')})")
    else:
        lines.append("- Runs in: Current context (inline)")

    if skill.get('allowed_tools'):
        lines.append(f"- Tools: {', '.join(skill['allowed_tools'])}")

    lines.append("")

    # Show alternatives if any
    if show_alternatives and result.get('alternatives'):
        lines.append("Other possible matches:")
        for name, alt_score in result['alternatives']:
            lines.append(f"- {name} (score: {alt_score:.1f})")
        lines.append("")

    lines.append("**Would you like me to load this skill?**")

    return "\n".join(lines)


def main():
    """Main entry point."""
    args = sys.argv[1:]

    # Parse options
    auto_load = '--auto-load' in args or '--load' in args
    json_output = '--json' in args
    threshold = 3.0

    # Parse threshold
    if '--threshold' in args:
        idx = args.index('--threshold')
        if idx + 1 < len(args):
            try:
                threshold = float(args[idx + 1])
            except ValueError:
                pass
            args = args[:idx] + args[idx + 2:]
        else:
            args = args[:idx]

    # Remove flags
    for flag in ['--auto-load', '--load', '--json']:
        if flag in args:
            args.remove(flag)

    if '--help' in args or '-h' in args or not args:
        print("Usage: python discover_skill.py <query> [OPTIONS]")
        print("")
        print("Discover and optionally load a skill matching the query.")
        print("")
        print("Arguments:")
        print("  query           User's task/intent (e.g., 'search and fix bugs')")
        print("")
        print("Options:")
        print("  --auto-load     Automatically output full skill content if found")
        print("  --threshold N   Minimum search score (default: 3.0)")
        print("  --json          Output as JSON")
        print("  --help, -h      Show this help")
        print("")
        print("Examples:")
        print("  python discover_skill.py 'find and fix issues'")
        print("  python discover_skill.py 'search edit' --auto-load")
        return

    query = ' '.join(args)

    # Discover
    result = discover_skill(query, min_score=threshold, auto_load=auto_load)

    # Output
    if json_output:
        import json
        # Remove content from JSON output (too large)
        output = {k: v for k, v in result.items() if k != 'content'}
        print(json.dumps(output, indent=2, default=str))
    elif auto_load and result.get('content'):
        # If auto-loading, just output the skill content
        print(result['content'])
    else:
        # Interactive mode - show discovery prompt
        print(format_discovery_output(result))


if __name__ == "__main__":
    main()
