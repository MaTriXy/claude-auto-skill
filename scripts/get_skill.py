#!/usr/bin/env python3
"""
Get Skill Script

Loads the full content of a specific auto-generated skill.
This is the lazy-loading mechanism that retrieves skill instructions on demand,
making them immediately active in the current session.

Usage:
    python get_skill.py <skill-name>
    python get_skill.py <skill-name> --raw
    python get_skill.py <skill-name> --json
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent))
from skill_registry import load_registry, rebuild_registry, get_skills_dir


def find_skill(registry: Dict, name: str) -> Optional[Dict]:
    """Find a skill by name (case-insensitive, partial match)."""
    skills = registry.get('skills', [])
    name_lower = name.lower()

    # Exact match first
    for skill in skills:
        if skill['name'].lower() == name_lower:
            return skill

    # Partial match (contains)
    matches = [s for s in skills if name_lower in s['name'].lower()]
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        print(f"Multiple skills match '{name}':", file=sys.stderr)
        for m in matches:
            print(f"  - {m['name']}", file=sys.stderr)
        print("\nPlease specify the exact name.", file=sys.stderr)
        return None

    return None


def load_skill_content(skill: Dict) -> Optional[str]:
    """Load the full content of a skill file."""
    skill_path = Path(skill['path'])

    if not skill_path.exists():
        # Try relative to skills dir
        skill_path = get_skills_dir() / skill['name'] / "SKILL.md"

    if not skill_path.exists():
        print(f"Error: Skill file not found: {skill['path']}", file=sys.stderr)
        return None

    try:
        return skill_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading skill file: {e}", file=sys.stderr)
        return None


def extract_body(content: str) -> str:
    """Extract body (instructions) from skill content, stripping frontmatter."""
    if not content.startswith('---'):
        return content

    # Find closing ---
    end_idx = content.find('---', 3)
    if end_idx == -1:
        return content

    return content[end_idx + 3:].strip()


def format_skill_output(skill: Dict, content: str, raw: bool = False) -> str:
    """
    Format skill content for output.

    The formatted output uses clear delimiters that signal to Claude
    these are ACTIVE INSTRUCTIONS to follow when relevant.

    This bypasses Claude Code's normal skill discovery (which happens at
    session start) by injecting the skill content directly into the conversation.
    """
    if raw:
        return extract_body(content)

    lines = []
    lines.append("=" * 70)
    lines.append(f"SKILL LOADED: {skill['name']}")
    lines.append(f"Confidence: {skill.get('confidence', 0):.0%}")
    lines.append(f"Tokens: ~{skill.get('token_estimate', 0):,}")

    # Show execution context if set
    if skill.get('context') == 'fork':
        agent = skill.get('agent', 'general-purpose')
        lines.append(f"Execution: Isolated subagent ({agent})")
    else:
        lines.append("Execution: Inline (current context)")

    # Show allowed tools if restricted
    if skill.get('allowed_tools'):
        tools_str = ", ".join(skill['allowed_tools'])
        lines.append(f"Allowed tools: {tools_str}")

    if skill.get('pattern_id'):
        lines.append(f"Pattern: {skill.get('pattern_id')}")

    lines.append("=" * 70)
    lines.append("")

    # Add context-aware instructions
    if skill.get('context') == 'fork':
        lines.append("This skill is designed to run in ISOLATION (context: fork).")
        lines.append("When executing, spawn a subagent to handle this task separately.")
        lines.append("")
    else:
        lines.append("The following instructions are now ACTIVE for this session.")
        lines.append("Follow them when relevant to the user's requests.")
        lines.append("")

    # Add tool restriction notice if applicable
    if skill.get('allowed_tools'):
        tools_str = ", ".join(skill['allowed_tools'])
        lines.append(f"TOOL RESTRICTION: Only use these tools: {tools_str}")
        lines.append("")

    lines.append(extract_body(content))
    lines.append("")
    lines.append("=" * 70)
    lines.append("END OF SKILL - INSTRUCTIONS ARE NOW ACTIVE")
    lines.append("=" * 70)

    return "\n".join(lines)


def format_json_output(skill: Dict, content: str) -> str:
    """Format as JSON for programmatic use."""
    return json.dumps({
        'name': skill['name'],
        'summary': skill.get('summary', ''),
        'description': skill.get('description', ''),
        'confidence': skill.get('confidence', 0),
        'token_estimate': skill.get('token_estimate', 0),
        'keywords': skill.get('keywords', []),
        'pattern_id': skill.get('pattern_id', ''),
        'body': extract_body(content),
        'full_content': content
    }, indent=2)


def list_available_skills(registry: Dict) -> str:
    """List available skills when none specified."""
    skills = registry.get('skills', [])
    if not skills:
        return "No auto-generated skills found.\n\nRun /auto-skill:review to create skills from detected patterns."

    lines = ["## Available Auto-Generated Skills", ""]

    for skill in skills:
        confidence = skill.get('confidence', 0)
        summary = skill.get('summary', '')[:60]
        if len(skill.get('summary', '')) > 60:
            summary += "..."
        lines.append(f"- **{skill['name']}** ({confidence:.0%}) - {summary}")

    lines.append("")
    lines.append("Usage: `python scripts/get_skill.py <skill-name>`")
    lines.append("Or use: `/auto-skill:load <skill-name>`")

    return "\n".join(lines)


def main():
    """Main entry point."""
    args = sys.argv[1:]

    # Parse options
    json_output = '--json' in args
    raw_output = '--raw' in args
    rebuild = '--rebuild' in args

    for opt in ['--json', '--raw', '--rebuild']:
        if opt in args:
            args.remove(opt)

    if '--help' in args or '-h' in args:
        print("Usage: python get_skill.py <skill-name> [OPTIONS]")
        print("")
        print("Loads an auto-generated skill into the current session.")
        print("The output format signals to Claude that these are active instructions.")
        print("")
        print("Arguments:")
        print("  skill-name    Name of the skill to load (case-insensitive)")
        print("")
        print("Options:")
        print("  --json        Output as JSON with metadata")
        print("  --raw         Output raw body without delimiters")
        print("  --rebuild     Rebuild registry before loading")
        print("  --help, -h    Show this help")
        print("")
        print("Examples:")
        print("  python get_skill.py grep-edit-workflow")
        print("  python get_skill.py security --json")
        return

    # Load or rebuild registry
    if rebuild:
        registry = rebuild_registry()
    else:
        registry = load_registry()
        if not registry:
            registry = rebuild_registry()

    # Check if skill name provided
    if not args:
        print(list_available_skills(registry))
        return

    skill_name = ' '.join(args)

    # Find skill
    skill = find_skill(registry, skill_name)
    if not skill:
        print(f"Error: Skill '{skill_name}' not found.", file=sys.stderr)
        print("", file=sys.stderr)
        print(list_available_skills(registry), file=sys.stderr)
        sys.exit(1)

    # Load content
    content = load_skill_content(skill)
    if not content:
        sys.exit(1)

    # Output
    if json_output:
        print(format_json_output(skill, content))
    else:
        print(format_skill_output(skill, content, raw=raw_output))


if __name__ == "__main__":
    main()
