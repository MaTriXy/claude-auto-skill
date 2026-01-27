"""
Skill Generator - Enhanced v2 with rich metadata and contextual understanding.

Generates SKILL.md files with:
- V1: Tool patterns, confidence, execution context
- V2: Session analysis, code structure, design patterns, problem-solving approaches
"""

import re
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import yaml

from .pattern_detector import DetectedPattern


@dataclass
class SkillCandidate:
    """A skill candidate ready for user review (v1 + v2)."""

    pattern: DetectedPattern
    name: str
    description: str
    steps: list[str]
    output_path: Path
    yaml_frontmatter: dict
    # V1 execution context options
    use_fork: bool = False
    agent_type: Optional[str] = None
    allowed_tools: list[str] = field(default_factory=list)
    # V2 additions
    v2_content: Optional[dict] = None

    def render(self) -> str:
        """Render the skill as a SKILL.md file."""
        return SkillGenerator.render_skill_md(
            name=self.name,
            description=self.description,
            steps=self.steps,
            frontmatter=self.yaml_frontmatter,
            v2_content=self.v2_content,
        )


class SkillGenerator:
    """Generates SKILL.md files from detected patterns with v2 enhancements."""

    DEFAULT_OUTPUT_DIR = Path.home() / ".claude" / "skills" / "auto"

    # Tool step templates (V1)
    TOOL_STEP_TEMPLATES = {
        "Read": "Read the file to understand its contents",
        "Write": "Create/update the file with the required content",
        "Edit": "Edit the file to make the necessary changes",
        "Bash": "Run the required command",
        "Grep": "Search for patterns in the codebase",
        "Glob": "Find files matching the pattern",
        "WebFetch": "Fetch content from the URL",
        "WebSearch": "Search the web for information",
        "Task": "Delegate to a specialized agent",
    }

    # Tools classified by side effects (V1)
    READ_ONLY_TOOLS = {"Read", "Grep", "Glob", "WebFetch", "WebSearch"}
    MUTATING_TOOLS = {"Write", "Edit", "Bash", "NotebookEdit"}
    DELEGATION_TOOLS = {"Task"}
    FORK_SUGGESTING_TOOLS = {"Bash", "Task"}

    # Agent type heuristics (V1)
    AGENT_TYPE_HEURISTICS = {
        frozenset({"Read", "Grep"}): "Explore",
        frozenset({"Read", "Glob"}): "Explore",
        frozenset({"Grep", "Glob"}): "Explore",
        frozenset({"Grep", "Read", "Glob"}): "Explore",
        frozenset({"Read", "Task"}): "Plan",
    }

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize skill generator."""
        self.output_dir = output_dir or self.DEFAULT_OUTPUT_DIR

    def generate_candidate(
        self,
        pattern: DetectedPattern,
        force_fork: Optional[bool] = None,
        force_agent: Optional[str] = None,
        custom_allowed_tools: Optional[list[str]] = None,
    ) -> SkillCandidate:
        """Generate a skill candidate from a detected pattern (v1 + v2)."""
        tools = pattern.tool_sequence

        # V1: Generate base info
        name = self._generate_skill_name(pattern)
        description = self._generate_description(pattern)
        steps = self._generate_steps(pattern)

        # V1: Determine execution context
        use_fork = force_fork if force_fork is not None else self._should_use_fork(tools)
        agent_type = force_agent if force_agent is not None else self._determine_agent_type(tools)
        allowed_tools = custom_allowed_tools if custom_allowed_tools is not None else self._generate_allowed_tools(tools)

        # V1: Build frontmatter
        frontmatter = self._build_frontmatter(
            pattern=pattern,
            name=name,
            description=description,
            use_fork=use_fork,
            agent_type=agent_type,
            allowed_tools=allowed_tools,
        )

        # V2: Add enhanced content sections
        v2_content = self._build_v2_content(pattern) if hasattr(pattern, 'session_context') else None

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
            v2_content=v2_content,
        )

    def save_skill(self, candidate: SkillCandidate, update_registry: bool = True) -> Path:
        """Save a skill candidate to disk."""
        candidate.output_path.parent.mkdir(parents=True, exist_ok=True)

        content = candidate.render()
        candidate.output_path.write_text(content)

        # Update registry if available
        if update_registry:
            try:
                import sys
                scripts_dir = Path(__file__).parent.parent / "scripts"
                if scripts_dir.exists():
                    sys.path.insert(0, str(scripts_dir))
                    from skill_registry import add_skill_to_registry
                    add_skill_to_registry(candidate.output_path.parent)
            except (ImportError, FileNotFoundError):
                pass

        return candidate.output_path

    # V2: Enhanced content generation

    def _build_v2_content(self, pattern: DetectedPattern) -> Optional[dict]:
        """Build v2 content sections for the skill."""
        if not pattern.session_context and not pattern.code_context and not pattern.design_patterns:
            return None

        content = {}

        # Context section
        if pattern.session_context or pattern.design_patterns:
            content["context_section"] = self._build_context_section(pattern)

        # Design patterns section
        if pattern.design_patterns:
            content["patterns_section"] = self._build_patterns_section(pattern)

        # Code structure section
        if pattern.code_context:
            content["code_structure_section"] = self._build_code_structure_section(pattern)

        # Problem-solving approach (enhance steps)
        if pattern.problem_solving_approach:
            content["enhanced_steps"] = self._build_enhanced_steps(pattern)

        return content if content else None

    def _build_context_section(self, pattern: DetectedPattern) -> str:
        """Build the Context section."""
        lines = ["## Context\n"]

        if pattern.session_context:
            ctx = pattern.session_context
            lines.append("This workflow is most appropriate when:\n")

            if ctx.get("primary_intent"):
                intent_desc = {
                    "debug": "tracking down and fixing bugs",
                    "implement": "building new features",
                    "refactor": "improving code structure",
                    "test": "writing or improving tests",
                    "explore": "understanding existing code",
                    "document": "adding documentation",
                }.get(ctx["primary_intent"], ctx["primary_intent"])
                lines.append(f"- You are {intent_desc}\n")

            if ctx.get("problem_domains"):
                domains = ", ".join(ctx["problem_domains"][:3])
                lines.append(f"- Working in these areas: {domains}\n")

            if ctx.get("workflow_type"):
                lines.append(f"- Following a {ctx['workflow_type']} approach\n")

            if ctx.get("tool_success_rate"):
                rate = int(ctx["tool_success_rate"] * 100)
                lines.append(f"\nSuccess rate in previous usage: {rate}%\n")

        return "".join(lines)

    def _build_patterns_section(self, pattern: DetectedPattern) -> str:
        """Build the Detected Patterns section."""
        lines = ["## Detected Patterns\n"]

        if not pattern.design_patterns:
            return ""

        lines.append("This workflow incorporates these design patterns:\n\n")

        for dp in pattern.design_patterns[:3]:  # Top 3 patterns
            name = dp.get("name", "Unknown")
            confidence = int(dp.get("confidence", 0) * 100)
            desc = dp.get("description", "")
            pattern_type = dp.get("type", "")

            lines.append(f"### {name} ({pattern_type}, confidence: {confidence}%)\n")
            if desc:
                lines.append(f"- **Description:** {desc}\n")

            # Add context if available (from known patterns)
            context = self._get_pattern_context(name)
            if context:
                lines.append(f"- **When to use:** {context.get('when', 'N/A')}\n")
                if context.get("benefits"):
                    lines.append(f"- **Benefits:** {', '.join(context['benefits'][:2])}\n")

            indicators = dp.get("indicators", [])
            if indicators:
                lines.append(f"- **Detected from:** {indicators[0]}\n")

            lines.append("\n")

        return "".join(lines)

    def _build_code_structure_section(self, pattern: DetectedPattern) -> str:
        """Build the Code Structure Awareness section."""
        if not pattern.code_context:
            return ""

        lines = ["## Code Structure Awareness\n"]

        ctx = pattern.code_context
        if ctx.get("detected_symbols"):
            symbols = ctx["detected_symbols"]

            if symbols.get("classes"):
                lines.append("**Key Classes:**\n")
                for cls in symbols["classes"][:5]:
                    lines.append(f"- `{cls['name']}` ({cls['file']}:{cls['line']})\n")
                lines.append("\n")

            if symbols.get("functions"):
                lines.append("**Key Functions:**\n")
                for func in symbols["functions"][:5]:
                    lines.append(f"- `{func['name']}` ({func['file']}:{func['line']})\n")
                lines.append("\n")

        if ctx.get("dependencies"):
            lines.append("**Dependencies:**\n")
            for dep in ctx["dependencies"][:3]:
                lines.append(f"- {dep['source']} → {dep['target']} ({dep['type']})\n")
            lines.append("\n")

        return "".join(lines)

    def _build_enhanced_steps(self, pattern: DetectedPattern) -> list[str]:
        """Build enhanced steps with problem-solving approach."""
        approach = pattern.problem_solving_approach
        if not approach or not approach.get("steps"):
            return self._generate_steps(pattern)

        # Use approach steps if available
        steps = []
        for i, step in enumerate(approach["steps"][:6], 1):
            # Map to tools from pattern
            tool_hint = ""
            if i <= len(pattern.tool_sequence):
                tool = pattern.tool_sequence[i - 1]
                tool_hint = f" ({tool})"

            steps.append(f"{i}. {step}{tool_hint}")

        return steps

    def _get_pattern_context(self, pattern_name: str) -> Optional[dict]:
        """Get context for a known pattern."""
        contexts = {
            "MVC": {
                "when": "Building web applications with clear separation",
                "benefits": ["Separates concerns", "Easier testing"],
            },
            "Repository": {
                "when": "Abstracting data access layer",
                "benefits": ["Decouples business logic", "Testable"],
            },
            "TDD": {
                "when": "Building new features or fixing bugs",
                "benefits": ["Better coverage", "Refactoring confidence"],
            },
            "Refactor-Safe": {
                "when": "Improving code without changing behavior",
                "benefits": ["Maintains tests", "Reduces risk"],
            },
            "Factory": {
                "when": "Creating objects with complex initialization",
                "benefits": ["Centralized creation", "Flexible"],
            },
        }
        return contexts.get(pattern_name)

    # V1: Helper methods

    def _should_use_fork(self, tools: list[str]) -> bool:
        """Determine if skill should run in isolated context."""
        return bool(set(tools) & self.FORK_SUGGESTING_TOOLS)

    def _determine_agent_type(self, tools: list[str]) -> Optional[str]:
        """Determine recommended agent type."""
        tool_set = frozenset(tools)

        if tool_set in self.AGENT_TYPE_HEURISTICS:
            return self.AGENT_TYPE_HEURISTICS[tool_set]

        for heuristic_tools, agent_type in self.AGENT_TYPE_HEURISTICS.items():
            if tool_set <= heuristic_tools:
                return agent_type

        if tool_set <= self.READ_ONLY_TOOLS:
            return "Explore"
        if "Task" in tool_set:
            return "general-purpose"

        return None

    def _generate_allowed_tools(self, tools: list[str]) -> list[str]:
        """Generate allowed-tools list."""
        seen = set()
        unique = []
        for tool in tools:
            if tool not in seen:
                seen.add(tool)
                unique.append(tool)
        return unique
    
    def _generate_tags(self, pattern: DetectedPattern) -> list[str]:
        """
        Generate tags for Vercel skills.sh compatibility (Phase 3).
        
        Tags help with skill discovery and categorization.
        """
        tags = []
        
        # Add tool-based tags
        for tool in pattern.tool_sequence:
            tool_tag = tool.lower().replace("_", "-")
            if tool_tag not in tags:
                tags.append(tool_tag)
        
        # Add intent-based tags from session context
        if hasattr(pattern, 'session_context') and pattern.session_context:
            if pattern.session_context.get("primary_intent"):
                intent = pattern.session_context["primary_intent"]
                tags.append(intent)
            
            # Add workflow type as tag
            if pattern.session_context.get("workflow_type"):
                workflow = pattern.session_context["workflow_type"].lower().replace("_", "-")
                if workflow not in tags:
                    tags.append(workflow)
        
        # Add Mental domain tags
        if hasattr(pattern, 'mental_context') and pattern.mental_context:
            domains = pattern.mental_context.get("domains", [])
            for domain in domains[:3]:  # Limit to top 3 domains
                domain_tag = domain["name"].lower().replace(" ", "-")
                if domain_tag not in tags:
                    tags.append(domain_tag)
        
        # Add design pattern tags
        if hasattr(pattern, 'design_patterns') and pattern.design_patterns:
            for dp in pattern.design_patterns[:2]:  # Limit to top 2 patterns
                pattern_tag = dp["name"].lower().replace(" ", "-")
                if pattern_tag not in tags:
                    tags.append(pattern_tag)
        
        # Limit total tags to 10 for readability
        return tags[:10]

    def _generate_skill_name(self, pattern: DetectedPattern) -> str:
        """Generate kebab-case skill name."""
        if pattern.suggested_name:
            name = pattern.suggested_name
        else:
            tools = pattern.tool_sequence
            if len(tools) >= 2:
                name = f"{tools[0].lower()}-{tools[-1].lower()}-workflow"
            else:
                name = f"{tools[0].lower()}-workflow" if tools else "auto-workflow"

        name = re.sub(r"[^a-zA-Z0-9-]", "-", name)
        name = re.sub(r"-+", "-", name)
        name = name.strip("-").lower()

        return f"{name}-{pattern.id[:6]}"

    def _generate_description(self, pattern: DetectedPattern) -> str:
        """Generate description."""
        if pattern.suggested_description:
            return pattern.suggested_description

        tools = pattern.tool_sequence
        if len(tools) == 2:
            return f"Workflow: {tools[0]} then {tools[1]}"
        elif len(tools) > 2:
            return f"Workflow: {' → '.join(tools)}"
        return "Auto-detected workflow"

    def _generate_steps(self, pattern: DetectedPattern) -> list[str]:
        """Generate procedural steps."""
        steps = []
        for i, tool in enumerate(pattern.tool_sequence, 1):
            desc = self.TOOL_STEP_TEMPLATES.get(tool, f"Use {tool} tool")
            steps.append(f"{i}. {desc}")
        return steps

    def _build_frontmatter(
        self,
        pattern: DetectedPattern,
        name: str,
        description: str,
        use_fork: bool,
        agent_type: Optional[str],
        allowed_tools: list[str],
    ) -> dict:
        """Build YAML frontmatter with v1 + v2 metadata."""
        fm = {
            "name": name,
            "description": description,
        }

        if use_fork:
            fm["context"] = "fork"
            if agent_type:
                fm["agent"] = agent_type

        if allowed_tools:
            fm["allowed-tools"] = ", ".join(allowed_tools)

        # V1 metadata
        fm.update({
            "auto-generated": True,
            "confidence": round(pattern.confidence, 2),
            "occurrence-count": pattern.occurrence_count,
            "source-sessions": pattern.session_ids[:5],
            "first-seen": pattern.first_seen.isoformat(),
            "last-seen": pattern.last_seen.isoformat(),
            "pattern-id": pattern.id,
            "created-at": datetime.now(timezone.utc).isoformat(),
        })

        # V2 metadata
        if pattern.session_context:
            fm["session-analysis"] = pattern.session_context

        if pattern.code_context:
            fm["code-context"] = {
                "analyzed_files": pattern.code_context.get("analyzed_files", 0),
                "primary_languages": pattern.code_context.get("primary_languages", []),
            }

        if pattern.design_patterns:
            fm["design-patterns"] = pattern.design_patterns

        if pattern.problem_solving_approach:
            fm["problem-solving-approach"] = {
                "type": pattern.problem_solving_approach.get("type"),
                "description": pattern.problem_solving_approach.get("description"),
            }
        
        # Hybrid Phase 3: Mental context and Vercel metadata
        if hasattr(pattern, 'mental_context') and pattern.mental_context:
            fm["mental-context"] = {
                "domains": [d["name"] for d in pattern.mental_context.get("domains", [])],
                "capabilities": [c["name"] for c in pattern.mental_context.get("capabilities", [])],
                "aspects": [a["name"] for a in pattern.mental_context.get("aspects", [])]
                if pattern.mental_context.get("aspects") else [],
            }
        
        # Vercel skills.sh compatibility metadata
        fm["compatible-agents"] = ["claude-code", "opencode", "codex"]
        fm["tags"] = self._generate_tags(pattern)
        fm["source"] = "auto-generated"
        fm["derived-from"] = "local-patterns"

        return fm

    @staticmethod
    def render_skill_md(
        name: str,
        description: str,
        steps: list[str],
        frontmatter: dict,
        v2_content: Optional[dict] = None,
    ) -> str:
        """Render complete SKILL.md file."""
        yaml_content = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True)

        content = f"""---
{yaml_content.strip()}
---

# {name}

{description}

"""

        # V2: Add context sections
        if v2_content:
            if "context_section" in v2_content:
                content += v2_content["context_section"] + "\n"

            if "patterns_section" in v2_content:
                content += v2_content["patterns_section"] + "\n"

        # Steps (possibly enhanced with v2)
        steps_to_use = v2_content.get("enhanced_steps", steps) if v2_content else steps

        content += "## Steps\n\n"
        content += "\n".join(steps_to_use)
        content += "\n\n"

        # V2: Add code structure section
        if v2_content and "code_structure_section" in v2_content:
            content += v2_content["code_structure_section"] + "\n"

        # Footer
        content += """## Generated by Claude Auto-Skill v2

This skill was automatically detected from your usage patterns.
Confidence reflects how frequently and successfully this pattern was used.
"""

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
        """Delete an auto-generated skill."""
        import shutil

        skill_path = (self.output_dir / name).resolve()
        if not skill_path.is_relative_to(self.output_dir.resolve()):
            return False
        if skill_path.exists() and skill_path.is_dir():
            shutil.rmtree(skill_path)
            return True
        return False
