"""
Skill Generator - Converts detected patterns into SKILL.md files.

Generates valid Claude Code skills with proper YAML frontmatter,
procedural steps, and metadata for tracking auto-generated skills.

Supports Claude Code skill features:
- `context: fork` for running skills in isolated subagents
- `allowed-tools` for restricting tool access
- `agent` for specifying which subagent type to use
"""

import re
import textwrap
from dataclasses import dataclass, field
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
    # Execution context options
    use_fork: bool = False
    agent_type: Optional[str] = None
    allowed_tools: list[str] = field(default_factory=list)

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

    # Tools classified by their side effects
    # Read-only tools: safe, no side effects
    READ_ONLY_TOOLS = {"Read", "Grep", "Glob", "WebFetch", "WebSearch"}

    # Mutating tools: can modify files or system state
    MUTATING_TOOLS = {"Write", "Edit", "Bash", "NotebookEdit"}

    # Delegation tools: spawn subprocesses or agents
    DELEGATION_TOOLS = {"Task"}

    # Tools that suggest the skill should run in isolation (context: fork)
    # Bash is included because it can have arbitrary side effects
    FORK_SUGGESTING_TOOLS = {"Bash", "Task"}

    # Mapping from pattern characteristics to recommended agent types
    AGENT_TYPE_HEURISTICS = {
        # Exploration patterns (read-only)
        frozenset({"Read", "Grep"}): "Explore",
        frozenset({"Read", "Glob"}): "Explore",
        frozenset({"Grep", "Glob"}): "Explore",
        frozenset({"Grep", "Read", "Glob"}): "Explore",
        # Planning patterns
        frozenset({"Read", "Task"}): "Plan",
    }

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the skill generator.

        Args:
            output_dir: Directory to write skills to. Defaults to ~/.claude/skills/auto/
        """
        self.output_dir = output_dir or self.DEFAULT_OUTPUT_DIR

    def _should_use_fork(self, tools: list[str]) -> bool:
        """
        Determine if a skill should run in an isolated subagent context.

        Skills with side effects (Bash, Task) benefit from isolation to:
        - Prevent unintended modifications to the main conversation context
        - Allow focused execution without conversation history
        - Enable cleaner error handling and rollback

        Args:
            tools: List of tool names in the pattern

        Returns:
            True if the skill should use context: fork
        """
        tool_set = set(tools)

        # If pattern contains tools that suggest side effects, use fork
        if tool_set & self.FORK_SUGGESTING_TOOLS:
            return True

        # If pattern is purely mutating (Write, Edit) without read context,
        # it might be a destructive pattern - suggest fork for safety
        if tool_set <= self.MUTATING_TOOLS and len(tool_set) > 1:
            return True

        return False

    def _determine_agent_type(self, tools: list[str]) -> Optional[str]:
        """
        Determine the recommended agent type for a pattern.

        Agent types affect:
        - Available tools and permissions
        - System prompt and behavior
        - Model used for execution

        Args:
            tools: List of tool names in the pattern

        Returns:
            Agent type string (e.g., "Explore", "Plan") or None for default
        """
        tool_set = frozenset(tools)

        # Check for exact matches first
        if tool_set in self.AGENT_TYPE_HEURISTICS:
            return self.AGENT_TYPE_HEURISTICS[tool_set]

        # Check for subset matches (pattern tools are subset of heuristic)
        for heuristic_tools, agent_type in self.AGENT_TYPE_HEURISTICS.items():
            if tool_set <= heuristic_tools:
                return agent_type

        # Heuristics based on tool characteristics
        if tool_set <= self.READ_ONLY_TOOLS:
            return "Explore"  # Read-only patterns suit exploration

        if "Task" in tool_set:
            return "general-purpose"  # Delegation needs full capabilities

        # Default: no specific agent (uses general-purpose)
        return None

    def _generate_allowed_tools(self, tools: list[str]) -> list[str]:
        """
        Generate the allowed-tools list for a skill.

        This restricts Claude to only use tools that are part of the pattern,
        preventing scope creep and ensuring predictable behavior.

        Args:
            tools: List of tool names in the pattern

        Returns:
            List of allowed tool specifications
        """
        allowed = []

        for tool in tools:
            if tool == "Bash":
                # Bash needs more specific permissions in real usage
                # For now, allow general Bash but note it could be restricted
                allowed.append("Bash")
            elif tool == "Task":
                # Task tool for delegation
                allowed.append("Task")
            else:
                # Standard tools
                allowed.append(tool)

        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for tool in allowed:
            if tool not in seen:
                seen.add(tool)
                unique.append(tool)

        return unique

    def _is_read_only_pattern(self, tools: list[str]) -> bool:
        """Check if a pattern is purely read-only (no side effects)."""
        return set(tools) <= self.READ_ONLY_TOOLS

    def generate_candidate(
        self,
        pattern: DetectedPattern,
        force_fork: Optional[bool] = None,
        force_agent: Optional[str] = None,
        custom_allowed_tools: Optional[list[str]] = None,
    ) -> SkillCandidate:
        """
        Generate a skill candidate from a detected pattern.

        Args:
            pattern: The detected pattern to convert
            force_fork: Override fork detection (None = auto-detect)
            force_agent: Override agent type (None = auto-detect)
            custom_allowed_tools: Override allowed tools (None = auto-generate)

        Returns:
            SkillCandidate ready for review and saving
        """
        tools = pattern.tool_sequence

        # Generate skill name
        name = self._generate_skill_name(pattern)

        # Generate description
        description = self._generate_description(pattern)

        # Generate procedural steps
        steps = self._generate_steps(pattern)

        # Determine execution context
        use_fork = force_fork if force_fork is not None else self._should_use_fork(tools)
        agent_type = force_agent if force_agent is not None else self._determine_agent_type(tools)
        allowed_tools = custom_allowed_tools if custom_allowed_tools is not None else self._generate_allowed_tools(tools)

        # Build frontmatter with execution context
        frontmatter = self._build_frontmatter(
            pattern=pattern,
            name=name,
            description=description,
            use_fork=use_fork,
            agent_type=agent_type,
            allowed_tools=allowed_tools,
        )

        # Determine output path
        output_path = self.output_dir / name / "SKILL.md"

        return SkillCandidate(
            pattern=pattern,
            name=name,
            description=description,
            steps=steps,
            output_path=output_path,
            yaml_frontmatter=frontmatter,
            use_fork=use_fork,
            agent_type=agent_type,
            allowed_tools=allowed_tools,
        )

    def save_skill(self, candidate: SkillCandidate, update_registry: bool = True) -> Path:
        """
        Save a skill candidate to disk and optionally update the registry.

        Args:
            candidate: The skill candidate to save
            update_registry: Whether to update the skill registry (default True)

        Returns:
            Path to the saved SKILL.md file
        """
        # Create directory
        candidate.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Render and write
        content = candidate.render()
        candidate.output_path.write_text(content)

        # Update the skill registry for dynamic loading
        if update_registry:
            try:
                import sys
                scripts_dir = Path(__file__).parent.parent / "scripts"
                sys.path.insert(0, str(scripts_dir))
                from skill_registry import add_skill_to_registry
                add_skill_to_registry(candidate.output_path.parent)
            except ImportError:
                pass  # Registry not available, skip

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
        use_fork: bool = False,
        agent_type: Optional[str] = None,
        allowed_tools: Optional[list[str]] = None,
    ) -> dict:
        """
        Build YAML frontmatter for the skill.

        Includes Claude Code skill features:
        - `context: fork` for running in isolated subagent
        - `agent` for specifying subagent type
        - `allowed-tools` for restricting tool access

        Args:
            pattern: The detected pattern
            name: Skill name
            description: Skill description
            use_fork: Whether to run in isolated context
            agent_type: Which agent type to use (e.g., "Explore", "Plan")
            allowed_tools: List of tools Claude can use

        Returns:
            Dict ready for YAML serialization
        """
        frontmatter = {
            "name": name,
            "description": description,
        }

        # Add execution context if fork is enabled
        if use_fork:
            frontmatter["context"] = "fork"
            if agent_type:
                frontmatter["agent"] = agent_type

        # Add allowed-tools if specified and non-empty
        if allowed_tools:
            # Format as comma-separated string per Claude Code spec
            frontmatter["allowed-tools"] = ", ".join(allowed_tools)

        # Add auto-generation metadata
        frontmatter.update({
            "auto-generated": True,
            "confidence": round(pattern.confidence, 2),
            "occurrence-count": pattern.occurrence_count,
            "source-sessions": pattern.session_ids[:5],  # Limit to 5
            "first-seen": pattern.first_seen.isoformat(),
            "last-seen": pattern.last_seen.isoformat(),
            "pattern-id": pattern.id,
            "created-at": datetime.now(timezone.utc).isoformat(),
        })

        return frontmatter

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

    def delete_skill(self, name: str, update_registry: bool = True) -> bool:
        """Delete an auto-generated skill by name."""
        import shutil

        skill_path = (self.output_dir / name).resolve()
        # Prevent path traversal attacks
        if not skill_path.is_relative_to(self.output_dir.resolve()):
            return False
        if skill_path.exists() and skill_path.is_dir():
            shutil.rmtree(skill_path)

            # Update the skill registry
            if update_registry:
                try:
                    import sys
                    scripts_dir = Path(__file__).parent.parent / "scripts"
                    sys.path.insert(0, str(scripts_dir))
                    from skill_registry import remove_skill_from_registry
                    remove_skill_from_registry(name)
                except ImportError:
                    pass  # Registry not available, skip

            return True
        return False
