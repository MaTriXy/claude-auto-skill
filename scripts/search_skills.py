#!/usr/bin/env python3
"""
Search Skills Script

Searches the skill registry for skills matching a query.
Uses keyword matching and fuzzy search to find relevant skills.

Usage:
    python search_skills.py "search files and edit"
    python search_skills.py grep --top 5
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent))
from skill_registry import load_registry, rebuild_registry


def tokenize(text: str) -> List[str]:
    """Tokenize text into searchable terms."""
    # Lowercase and split on non-alphanumeric
    import re
    return [t.lower() for t in re.split(r'[^a-zA-Z0-9]+', text) if t]


def score_skill(skill: Dict, query_tokens: List[str]) -> float:
    """
    Score a skill against query tokens.

    Factors:
    - Keyword matches (exact)
    - Name matches
    - Summary/description matches
    - Confidence boost
    """
    score = 0.0

    skill_name = skill['name'].lower()
    skill_keywords = [k.lower() for k in skill.get('keywords', [])]
    skill_summary = skill.get('summary', '').lower()
    skill_description = skill.get('description', '').lower()

    for token in query_tokens:
        # Exact keyword match: +3
        if token in skill_keywords:
            score += 3.0

        # Name contains token: +2
        if token in skill_name:
            score += 2.0

        # Summary contains: +1
        if token in skill_summary:
            score += 1.0

        # Description contains: +0.5
        if token in skill_description:
            score += 0.5

    # Boost by confidence (0-1 range, max +1)
    score += skill.get('confidence', 0) * 1.0

    return score


def search_skills(registry: Dict, query: str, top_n: int = 10) -> List[Tuple[Dict, float]]:
    """Search skills and return ranked results."""
    skills = registry.get('skills', [])
    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    # Score all skills
    scored = []
    for skill in skills:
        score = score_skill(skill, query_tokens)
        if score > 0:
            scored.append((skill, score))

    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    return scored[:top_n]


def format_results(results: List[Tuple[Dict, float]], query: str) -> str:
    """Format search results for display."""
    if not results:
        return f"No skills found matching '{query}'.\n\nTry different keywords or run /auto-skill:review to create new skills."

    lines = [f"## Skills matching '{query}'", ""]

    for skill, score in results:
        confidence = skill.get('confidence', 0)
        tokens = skill.get('token_estimate', 0)
        summary = skill.get('summary', '')[:50]
        if len(skill.get('summary', '')) > 50:
            summary += "..."

        lines.append(f"### {skill['name']} (score: {score:.1f})")
        lines.append(f"- Confidence: {confidence:.0%}, Tokens: ~{tokens:,}")
        lines.append(f"- {summary}")
        lines.append(f"- Keywords: {', '.join(skill.get('keywords', [])[:5])}")
        lines.append("")

    lines.append("Load a skill: `python scripts/get_skill.py <name>`")

    return "\n".join(lines)


def main():
    """Main entry point."""
    args = sys.argv[1:]

    # Parse options
    top_n = 10
    if '--top' in args:
        idx = args.index('--top')
        if idx + 1 < len(args):
            try:
                top_n = int(args[idx + 1])
            except ValueError:
                pass
            args = args[:idx] + args[idx + 2:]
        else:
            args = args[:idx]

    if '--help' in args or '-h' in args:
        print("Usage: python search_skills.py <query> [OPTIONS]")
        print("")
        print("Search for auto-generated skills by intent or keywords.")
        print("")
        print("Arguments:")
        print("  query         Search terms (e.g., 'search and edit files')")
        print("")
        print("Options:")
        print("  --top N       Return top N results (default: 10)")
        print("  --help, -h    Show this help")
        print("")
        print("Examples:")
        print("  python search_skills.py 'grep edit'")
        print("  python search_skills.py 'code review' --top 5")
        return

    if not args:
        print("Usage: python search_skills.py <query>")
        print("Example: python search_skills.py 'search and edit'")
        return

    query = ' '.join(args)

    # Load registry
    registry = load_registry()
    if not registry:
        registry = rebuild_registry()

    # Search
    results = search_skills(registry, query, top_n)

    # Output
    print(format_results(results, query))


if __name__ == "__main__":
    main()
