# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Auto-Skill** is a system that automatically generates Claude Code skills by observing workflow patterns, detecting repetition, and codifying successful procedures into reusable SKILL.md files. It enables Claude to learn from interactions and create skills autonomously, reducing manual skill creation.

**Install:** `npx skills add MaTriXy/auto-skill`

## Architecture

The system follows a pipeline architecture with three main stages:

### 1. Observer (Event Capture)
- Hooks into Claude Code's tool execution flow via `hooks/hooks.json`
- Captures workflow events including tool calls, outcomes, and context
- Stores events in a local SQLite database (`~/.claude/auto-skill/events.db`)
- Implementation: `hooks/observer.py`

### 2. Detector (Pattern Recognition)
- Analyzes captured events for reusable patterns
- Detection triggers:
  - **Repetition**: Same tool sequence 3+ times
  - **Success patterns**: High success rate on similar tasks
  - **User corrections**: User redirects Claude's approach
  - **Explicit teaching**: User provides domain knowledge
  - **Error recovery**: Successful self-correction patterns
- Session analysis detects intent (debug, implement, refactor, test)
- 18 design patterns recognized (MVC, TDD, Factory, etc.)
- Implementation: `core/pattern_detector.py`, `core/session_analyzer.py`, `core/design_pattern_detector.py`

### 3. Skill Forge (Skill Generation)
- Generates valid SKILL.md files from detected patterns
- Auto-generates YAML frontmatter with metadata
- Extracts procedural steps and embedded code
- Stores skills in `~/.claude/skills/auto/`
- Implementation: `core/skill_generator.py`

### Human-in-the-Loop
- Skills require user confirmation before activation
- Users can customize, ignore, or blacklist patterns
- Confidence scores guide when to suggest skills

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Implementation** | Claude Code Plugin | Hooks for observation, skills for output |
| **Distribution** | `npx skills add` | Zero-install via Skills CLI |
| **Detection scope** | Per-project + global | Project-specific patterns with cross-agent sharing |
| **Confirmation model** | Always confirm before activation | Prevents unwanted or incorrect skills |
| **Skill storage** | Local filesystem | Simplicity, matches existing skill system |
| **External discovery** | Skills.sh + well-known | 27,000+ community skills, RFC 8615 endpoints |

## File Structure

```
/core/               # Core modules (pattern detection, skill generation, telemetry)
/core/providers/     # Pluggable skill source providers (local, skillssh, wellknown)
/commands/           # CLI commands and slash command definitions
/hooks/              # Event capture hooks (observer.py, hooks.json)
/scripts/            # Utility scripts (skill registry, discovery)
/skills/             # Plugin skills (SKILL.md files)
/tests/              # Unit and integration tests
/web/                # Web UI dashboard (Flask)
/website/            # Documentation site (Docusaurus)
```

## Technical Constraints

- Must generate valid SKILL.md files compatible with Claude Code's skill system
- YAML frontmatter must include `name` and `description` at minimum
- Auto-generated skills should be clearly marked (`auto-generated: true`)
- Skills should track source sessions for debugging/refinement
- Pattern detection must avoid false positives (high precision preferred)

## Integration Points

- **Claude Code Skills System**: Outputs compatible SKILL.md format
- **Skills CLI**: Installable via `npx skills add MaTriXy/auto-skill`
- **Skills.sh**: External skill discovery and publishing
- **Multi-Agent**: Supports 10 coding agents with cross-agent skill sharing via symlinks
- **User Workflow**: Non-intrusive observation, confirmation-based activation

## Development

```bash
git clone https://github.com/MaTriXy/auto-skill.git
cd auto-skill
uv sync --all-extras
uv run pytest tests/ -v
```

## References

- [Skills CLI](https://github.com/vercel-labs/skills): `npx skills add` distribution
- [Claude Code Skills docs](https://docs.anthropic.com/en/docs/claude-code/skills): SKILL.md format
- [agentskills.io](https://agentskills.io): Skill spec compliance
- [Skills.sh](https://skills.sh): Community skill registry
