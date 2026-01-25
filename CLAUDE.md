# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Claude Auto-Skill** is a system that automatically generates Claude Code skills by observing workflow patterns, detecting repetition, and codifying successful procedures into reusable SKILL.md files. The goal is to enable Claude to learn from interactions and create skills autonomously, reducing manual skill creation.

## Architecture

The system follows a pipeline architecture with three main stages:

### 1. Observer (Event Capture)
- Hooks into Claude Code's tool execution flow
- Captures workflow events including tool calls, outcomes, and context
- Stores events in a local pattern database
- Implementation: Hook system or MCP server receiving telemetry

### 2. Detector (Pattern Recognition)
- Analyzes captured events for reusable patterns
- Detection triggers:
  - **Repetition**: Same tool sequence 3+ times
  - **Success patterns**: High success rate on similar tasks
  - **User corrections**: User redirects Claude's approach
  - **Explicit teaching**: User provides domain knowledge
  - **Error recovery**: Successful self-correction patterns

### 3. Skill Forge (Skill Generation)
- Generates valid SKILL.md files from detected patterns
- Auto-generates YAML frontmatter with metadata
- Extracts procedural steps and embedded code
- Stores skills in `~/.claude/skills/generated/` or `~/.claude/skills/auto/`

### Human-in-the-Loop
- Skills require user confirmation before activation
- Users can customize, ignore, or blacklist patterns
- Confidence scores guide when to suggest skills

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Implementation approach** | TBD: Plugin vs MCP vs Hybrid | Depends on access to Claude Code internals |
| **Detection scope** | TBD: Per-project vs Global | Project-specific = relevance; Global = reuse |
| **Confirmation model** | Always confirm before activation | Prevents unwanted or incorrect skills |
| **Skill storage** | Local filesystem initially | Simplicity, matches existing skill system |

## Development Roadmap

1. **Observer Hook**: Build event capture mechanism
2. **Pattern Grammar**: Define formal pattern matching rules
3. **Detection Heuristics**: Implement pattern recognition
4. **Skill Template Generator**: Auto-generate SKILL.md format
5. **Confirmation UX**: User approval interface
6. **Iteration**: Refine based on real-world usage

## Technical Constraints

- Must generate valid SKILL.md files compatible with Claude Code's skill system
- YAML frontmatter must include `name` and `description` at minimum
- Auto-generated skills should be clearly marked (`auto-generated: true`)
- Skills should track source sessions for debugging/refinement
- Pattern detection must avoid false positives (high precision preferred)

## File Structure (Planned)

```
/hooks/              # Event capture hooks
/detector/           # Pattern recognition engine
/forge/              # SKILL.md generation
/storage/            # Pattern database
/tests/              # Unit and integration tests
```

## Integration Points

- **Claude Code Skills System**: Must output compatible SKILL.md format
- **User Workflow**: Non-intrusive observation, confirmation-based activation
- **Existing Skills**: Can reference or build upon manually-created skills
- **Project Context**: May need to read project files to understand patterns

## References

- Anthropic Engineering Blog: Future vision explicitly mentions autonomous skill creation
- Claude Code Skills documentation: SKILL.md format and progressive disclosure
- Planning document: `auto-skill-plan.md` contains detailed architecture proposals
