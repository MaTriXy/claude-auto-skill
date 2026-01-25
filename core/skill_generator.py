"""
Skill Generator - Converts detected patterns into SKILL.md files.

Generates valid Claude Code skills with proper YAML frontmatter,
procedural steps, and metadata for tracking auto-generated skills.
"""

import re
import textwrap
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .pattern_detector import DetectedPattern


@dataclass
class SkillCandidate:
    """A skill candidate ready for user review."""

    pattern: DetectedPattern
    name: str
    description: str
    steps: list[str]
    output_path: Path
    yaml_frontmatter: dict

    def render(self) -> str:
        """Render the skill as a SKILL.md file."""
        return SkillGenerator.render_skill_md(
            name=self.name,
            description=self.description,
            steps=self.steps,
            frontmatter=self.yaml_frontmatter,
        )


class SkillGenerator:
    """Generates SKILL.md files from detected patterns."""

    # Default output directory for auto-generated skills
    DEFAULT_OUTPUT_DIR = Path.home() / ".claude" / "skills" / "auto"

    # Tool descriptions for generating steps
    TOOL_STEP_TEMPLATES = {
        "Read": "Read the file `{file_path}` to understand its contents",
        "Write": "Create/update the file `{file_path}` with the required content",
        "Edit": "Edit the file `{file_path}` to make the necessary changes",
        "Bash": "Run the command: `{command}`",
        "Grep": "Search for `{pattern}` in the codebase",
        "Glob": "Find files matching `{pattern}`",
        "WebFetch": "Fetch content from `{url}`",
        "WebSearch": "Search the web for: {query}",
        "Task": "Delegate to a specialized agent for {description}",
    }

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the skill generator.

        Args:
            output_dir: Directory to write skills to. Defaults to ~/.claude/skills/auto/
        """
        self.output_dir = output_dir or self.DEFAULT_OUTPUT_DIR

    def generate_candidate(self, pattern: DetectedPattern) -> SkillCandidate:
        """
        Generate a skill candidate from a detected pattern.

        Args:
            pattern: The detected pattern to convert

        Returns:
            SkillCandidate ready for review and saving
        """
        # Generate skill name
        name = self._generate_skill_name(pattern)

        # Generate description
        description = self._generate_description(pattern)

        # Generate procedural steps
        steps = self._generate_steps(pattern)

        # Build frontmatter
        frontmatter = self._build_frontmatter(pattern, name, description)

        # Determine output path
        output_path = self.output_dir / name / "SKILL.md"

        return SkillCandidate(
            pattern=pattern,
            name=name,
            description=description,
            steps=steps,
            output_path=output_path,
            yaml_frontmatter=frontmatter,
        )

    def save_skill(self, candidate: SkillCandidate) -> Path:
        """
        Save a skill candidate to disk.

        Args:
            candidate: The skill candidate to save

        Returns:
            Path to the saved SKILL.md file
        """
        # Create directory
        candidate.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Render and write
        content = candidate.render()
        candidate.output_path.write_text(content)

        return candidate.output_path

    def _generate_skill_name(self, pattern: DetectedPattern) -> str:
        """Generate a kebab-case skill name from pattern."""
        if pattern.suggested_name:
            name = pattern.suggested_name
        else:
            # Create from tool sequence
            tools = pattern.tool_sequence
            if len(tools) >= 2:
                name = f"{tools[0].lower()}-{tools[-1].lower()}-workflow"
            else:
                name = f"{tools[0].lower()}-workflow" if tools else "auto-workflow"

        # Sanitize to kebab-case
        name = re.sub(r"[^a-zA-Z0-9-]", "-", name)
        name = re.sub(r"-+", "-", name)
        name = name.strip("-").lower()

        # Add unique suffix from pattern ID
        return f"{name}-{pattern.id[:6]}"

    def _generate_description(self, pattern: DetectedPattern) -> str:
        """Generate a human-readable description."""
        tools = pattern.tool_sequence

        if len(tools) == 2:
            return f"Workflow that {self._tool_verb(tools[0])}s then {self._tool_verb(tools[1])}s"
        elif len(tools) > 2:
            middle = ", ".join(self._tool_verb(t) for t in tools[1:-1])
            return f"Workflow: {self._tool_verb(tools[0])} -> {middle} -> {self._tool_verb(tools[-1])}"
        else:
            return f"Auto-detected workflow pattern"

    def _tool_verb(self, tool_name: str) -> str:
        """Get a verb form of a tool name."""
        verbs = {
            "Read": "read",
            "Write": "write",
            "Edit": "edit",
            "Bash": "execute",
            "Grep": "search",
            "Glob": "find",
            "WebFetch": "fetch",
            "WebSearch": "search",
            "Task": "delegate",
        }
        return verbs.get(tool_name, tool_name.lower())

    def _generate_steps(self, pattern: DetectedPattern) -> list[str]:
        """Generate procedural steps from the tool sequence."""
        steps = []

        for i, tool in enumerate(pattern.tool_sequence):
            template = self.TOOL_STEP_TEMPLATES.get(tool)
            if template:
                # Create a generic step (actual parameters would vary)
                step = self._create_generic_step(tool, i + 1)
            else:
                step = f"Use the {tool} tool"

            steps.append(f"{i + 1}. {step}")

        return steps

    def _create_generic_step(self, tool: str, step_num: int) -> str:
        """Create a generic step description for a tool."""
        descriptions = {
            "Read": "Read the relevant file(s) to understand the current state",
            "Write": "Create or update the file with the required content",
            "Edit": "Make the necessary edits to the file",
            "Bash": "Run the required shell command",
            "Grep": "Search for the relevant patterns in the codebase",
            "Glob": "Find files matching the required pattern",
            "WebFetch": "Fetch content from the relevant URL",
            "WebSearch": "Search the web for relevant information",
            "Task": "Delegate to a specialized agent if needed",
        }
        return descriptions.get(tool, f"Use the {tool} tool as needed")

    def _build_frontmatter(
        self,
        pattern: DetectedPattern,
        name: str,
        description: str,
    ) -> dict:
        """Build YAML frontmatter for the skill."""
        return {
            "name": name,
            "description": description,
            "auto-generated": True,
            "confidence": round(pattern.confidence, 2),
            "occurrence-count": pattern.occurrence_count,
            "source-sessions": pattern.session_ids[:5],  # Limit to 5
            "first-seen": pattern.first_seen.isoformat(),
            "last-seen": pattern.last_seen.isoformat(),
            "pattern-id": pattern.id,
            "created-at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def render_skill_md(
        name: str,
        description: str,
        steps: list[str],
        frontmatter: dict,
        additional_content: str = "",
    ) -> str:
        """
        Render a complete SKILL.md file.

        Args:
            name: Skill name
            description: Skill description
            steps: List of procedural steps
            frontmatter: YAML frontmatter dict
            additional_content: Optional additional markdown content

        Returns:
            Complete SKILL.md content as string
        """
        import yaml

        # Build YAML frontmatter
        yaml_content = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)

        # Build steps section
        steps_content = "\n".join(steps)

        # Compose full document
        content = f"""---
{yaml_content.strip()}
---

# {name}

{description}

## Steps

{steps_content}
"""

        if additional_content:
            content += f"\n## Additional Notes\n\n{additional_content}\n"

        return content

    def list_generated_skills(self) -> list[Path]:
        """List all auto-generated skills."""
        if not self.output_dir.exists():
            return []

        skills = []
        for skill_dir in self.output_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    skills.append(skill_file)

        return sorted(skills)

    def delete_skill(self, name: str) -> bool:
        """Delete an auto-generated skill by name."""
        import shutil

        skill_path = (self.output_dir / name).resolve()
        # Prevent path traversal attacks
        if not skill_path.is_relative_to(self.output_dir.resolve()):
            return False
        if skill_path.exists() and skill_path.is_dir():
            shutil.rmtree(skill_path)
            return True
        return False
