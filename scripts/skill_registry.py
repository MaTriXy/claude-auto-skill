#!/usr/bin/env python3
"""
Skill Registry Manager

Maintains a lightweight index of auto-generated skills for efficient discovery
and on-demand loading. Mirrors the agent-registry pattern.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import re


def get_skills_dir() -> Path:
    """Get the directory where auto-generated skills are stored."""
    # Primary location
    primary = Path.home() / ".claude" / "skills" / "auto"
    if primary.exists():
        return primary

    # Fallback to project-local
    project = Path.cwd() / ".claude" / "skills" / "auto"
    if project.exists():
        return project

    # Return primary even if it doesn't exist yet
    return primary


def get_registry_path() -> Path:
    """Get the path to the skill registry."""
    script_dir = Path(__file__).parent.parent
    return script_dir / "references" / "registry.json"


def extract_frontmatter(content: str) -> Dict:
    """Extract YAML frontmatter from skill content using proper YAML parsing."""
    if not content.startswith('---'):
        return {}

    try:
        import yaml

        # Find the closing ---
        end_idx = content.find('---', 3)
        if end_idx == -1:
            return {}

        frontmatter_text = content[3:end_idx].strip()

        # Use yaml.safe_load for proper parsing
        result = yaml.safe_load(frontmatter_text)
        return result if isinstance(result, dict) else {}
    except Exception:
        return {}


def extract_body(content: str) -> str:
    """Extract the body (non-frontmatter) from skill content."""
    if not content.startswith('---'):
        return content

    end_idx = content.find('---', 3)
    if end_idx == -1:
        return content

    return content[end_idx + 3:].strip()


def estimate_tokens(text: str) -> int:
    """Rough token estimation (chars / 4)."""
    return len(text) // 4


def generate_keywords(content: str, name: str) -> List[str]:
    """Generate searchable keywords from skill content."""
    keywords = set()

    # Add name parts
    keywords.update(name.replace('-', ' ').split())

    # Extract tool names from content
    tool_pattern = r'\b(Read|Write|Edit|Bash|Grep|Glob|Task|WebFetch|WebSearch)\b'
    tools = re.findall(tool_pattern, content, re.IGNORECASE)
    keywords.update(t.lower() for t in tools)

    # Extract common action words
    actions = ['create', 'update', 'delete', 'search', 'find', 'check', 'validate',
               'build', 'test', 'deploy', 'review', 'fix', 'refactor']
    for action in actions:
        if action in content.lower():
            keywords.add(action)

    return sorted(keywords)


def scan_skill(skill_path: Path) -> Optional[Dict]:
    """Scan a single skill and return its registry entry."""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return None

    # Validate path is within expected skills directory (security check)
    try:
        skills_dir = get_skills_dir()
        resolved_path = skill_md.resolve()
        if not resolved_path.is_relative_to(skills_dir.resolve()):
            print(f"Warning: Skipping skill outside skills directory: {skill_path}")
            return None
    except (ValueError, RuntimeError):
        return None

    try:
        content = skill_md.read_text(encoding='utf-8')
        frontmatter = extract_frontmatter(content)
        body = extract_body(content)

        # Extract first paragraph as summary
        summary = ""
        for line in body.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                summary = line[:150]
                if len(line) > 150:
                    summary += "..."
                break

        # Parse allowed-tools (can be string or list)
        allowed_tools_raw = frontmatter.get('allowed-tools', '')
        if isinstance(allowed_tools_raw, str):
            allowed_tools = [t.strip() for t in allowed_tools_raw.split(',') if t.strip()]
        elif isinstance(allowed_tools_raw, list):
            allowed_tools = allowed_tools_raw
        else:
            allowed_tools = []

        return {
            'name': skill_path.name,
            'path': str(skill_md),
            'summary': summary or frontmatter.get('description', ''),
            'description': frontmatter.get('description', ''),
            'confidence': frontmatter.get('confidence', 0),
            'occurrences': frontmatter.get('occurrence-count', 0),
            'pattern_id': frontmatter.get('pattern-id', ''),
            'token_estimate': estimate_tokens(content),
            'keywords': generate_keywords(content, skill_path.name),
            'auto_generated': frontmatter.get('auto-generated', True),
            'created': frontmatter.get('created-at', ''),
            'last_seen': frontmatter.get('last-seen', ''),
            # Execution context fields
            'context': frontmatter.get('context', None),  # 'fork' or None
            'agent': frontmatter.get('agent', None),  # Agent type
            'allowed_tools': allowed_tools,
        }
    except Exception as e:
        print(f"Error scanning {skill_path}: {e}")
        return None


def build_registry() -> Dict:
    """Build the full registry by scanning all auto-generated skills."""
    skills_dir = get_skills_dir()

    skills = []
    total_tokens = 0

    if skills_dir.exists():
        for skill_path in skills_dir.iterdir():
            if skill_path.is_dir():
                entry = scan_skill(skill_path)
                if entry:
                    skills.append(entry)
                    total_tokens += entry['token_estimate']

    return {
        'version': '1.0',
        'generated': datetime.now().isoformat(),
        'skills_dir': str(skills_dir),
        'total_skills': len(skills),
        'total_tokens': total_tokens,
        'skills': sorted(skills, key=lambda x: x['name'])
    }


def save_registry(registry: Dict) -> Path:
    """Save registry to disk."""
    registry_path = get_registry_path()
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2)

    return registry_path


def load_registry() -> Optional[Dict]:
    """Load existing registry from disk."""
    registry_path = get_registry_path()

    if not registry_path.exists():
        return None

    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def add_skill_to_registry(skill_path: Path) -> bool:
    """Add or update a single skill in the registry."""
    registry = load_registry() or build_registry()

    entry = scan_skill(skill_path)
    if not entry:
        return False

    # Update or add
    skills = registry.get('skills', [])
    updated = False
    for i, skill in enumerate(skills):
        if skill['name'] == entry['name']:
            skills[i] = entry
            updated = True
            break

    if not updated:
        skills.append(entry)

    registry['skills'] = sorted(skills, key=lambda x: x['name'])
    registry['total_skills'] = len(skills)
    registry['total_tokens'] = sum(s['token_estimate'] for s in skills)
    registry['generated'] = datetime.now().isoformat()

    save_registry(registry)
    return True


def remove_skill_from_registry(skill_name: str) -> bool:
    """Remove a skill from the registry."""
    registry = load_registry()
    if not registry:
        return False

    skills = registry.get('skills', [])
    original_count = len(skills)
    skills = [s for s in skills if s['name'] != skill_name]

    if len(skills) == original_count:
        return False

    registry['skills'] = skills
    registry['total_skills'] = len(skills)
    registry['total_tokens'] = sum(s['token_estimate'] for s in skills)
    registry['generated'] = datetime.now().isoformat()

    save_registry(registry)
    return True


def rebuild_registry() -> Dict:
    """Force rebuild the registry from scratch."""
    registry = build_registry()
    save_registry(registry)
    return registry


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--rebuild':
        registry = rebuild_registry()
        print(f"Registry rebuilt: {registry['total_skills']} skills, ~{registry['total_tokens']:,} tokens")
    else:
        registry = load_registry()
        if registry:
            print(f"Registry loaded: {registry['total_skills']} skills")
        else:
            registry = rebuild_registry()
            print(f"Registry created: {registry['total_skills']} skills")
