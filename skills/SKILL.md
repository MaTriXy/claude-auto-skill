---
name: auto-skill-guide
description: Documentation for the Auto-Skill plugin - automatic workflow pattern detection, skill generation, and dynamic loading
---

# Auto-Skill Plugin

This plugin automatically detects workflow patterns from your Claude Code sessions, generates reusable skills, and can load them dynamically mid-session.

## ⚙️ CLI Tool Installation

The agent skills are now installed, but to use CLI commands like `auto-skill init`, `auto-skill discover`, etc., you need to install the Python package.

**Quick Install:**
```bash
# Option 1: Run the included install script
bash ~/.agents/skills/auto-skill-guide/install-cli.sh

# Option 2: Install from PyPI with uv (recommended)
uv pip install aiskill

# Option 3: Install from PyPI with pip
pip install aiskill
```

**Verify:** `auto-skill version`

---

## How It Works

```
Session 1: Grep → Read → Edit    ─┐
Session 2: Grep → Read → Edit     ├──▶ Pattern Detected → SKILL.md
Session 3: Grep → Read → Edit    ─┘
```

1. **Observation**: Every tool call is recorded via PostToolUse hook
2. **Detection**: Patterns are analyzed for repetition (3+ occurrences)
3. **Generation**: Approved patterns become SKILL.md files with proper frontmatter
4. **Discovery**: Claude proactively offers relevant skills for your tasks
5. **Loading**: Skills can be loaded mid-session without restart

## Commands

### /auto-skill:review

Review and approve detected patterns:

```
/auto-skill:review              # List all detected patterns
/auto-skill:review preview ID   # Preview a pattern as a skill
/auto-skill:review approve ID   # Generate skill from pattern
/auto-skill:review reject ID    # Dismiss a pattern
```

### /auto-skill:load

Load a generated skill into the current session:

```
/auto-skill:load                # List available skills
/auto-skill:load <name>         # Load specific skill immediately
```

Skills loaded this way become active immediately without requiring a session restart.

### /auto-skill:status

Show system diagnostics:

```
/auto-skill:status              # Display stats, patterns, and config
```

## Pattern Detection

Patterns are detected when:
- Same tool sequence appears 3+ times across sessions
- Sequence is 2-10 tools long
- Pattern has occurred within the last 7 days

### Confidence Scoring

| Factor | Weight | Description |
|--------|--------|-------------|
| Occurrences | 40% | More occurrences = higher confidence |
| Length | 20% | 3-5 tools is ideal |
| Success Rate | 25% | Successful patterns score higher |
| Recency | 15% | Recent patterns are prioritized |

### Example Patterns

```
Grep → Read → Edit        # Search, read context, make changes
Glob → Read → Write       # Find files, read, create new file
Read → Edit → Bash        # Read file, edit, run tests
```

## Dynamic Skill Loading

Unlike standard Claude Code skills (loaded at session start), auto-generated skills can be loaded **mid-session** using a registry system.

### How It Works

1. A lightweight registry indexes all skills (~metadata only)
2. Scripts retrieve and format skill content on demand
3. Output uses clear delimiters that signal active instructions:

```
======================================================================
SKILL LOADED: <name>
Confidence: <score>
Allowed tools: <tools>
======================================================================

<skill instructions>

======================================================================
END OF SKILL - INSTRUCTIONS ARE NOW ACTIVE
======================================================================
```

### Proactive Discovery

Claude can automatically discover relevant skills using the `skill-discovery` skill:

1. User requests a multi-step task
2. Claude searches for matching skills
3. If found, Claude asks: "Would you like me to load this skill?"
4. User approves → skill is loaded and followed

### Scripts

```bash
python scripts/list_skills.py           # List all skills
python scripts/search_skills.py "query" # Find by intent
python scripts/get_skill.py <name>      # Load specific skill
python scripts/discover_skill.py "task" # Discover + offer to load
python scripts/skill_registry.py --rebuild  # Refresh registry
```

## Execution Contexts

Generated skills automatically get appropriate execution settings:

| Pattern Type | Context | Agent | Why |
|-------------|---------|-------|-----|
| `Grep → Read` | Inline | Explore | Read-only, safe |
| `Read → Edit → Bash` | Fork | general-purpose | Has side effects |

**Inline**: Runs in current conversation context.

**Fork** (`context: fork`): Runs in isolated subagent. Use for:
- Tasks with side effects (deployments, builds)
- Workflows that shouldn't pollute conversation history
- Long-running operations

### Tool Restrictions

Generated skills include `allowed-tools` based on the pattern:

```yaml
allowed-tools: Grep, Read, Edit
```

This prevents scope creep and ensures predictable behavior.

## Generated Skills

Auto-generated skills are saved to:
```
~/.claude/skills/auto/<skill-name>/SKILL.md
```

Each skill includes:
- YAML frontmatter with metadata
- `auto-generated: true` flag
- `context: fork` if appropriate
- `allowed-tools` restrictions
- Confidence score and source sessions
- Procedural steps derived from the pattern

## Configuration

Detection thresholds (in `~/.claude/auto-skill.local.md`):

```yaml
---
detection:
  min_occurrences: 3      # Minimum pattern repetitions
  min_sequence_length: 2  # Shortest pattern
  max_sequence_length: 10 # Longest pattern
  lookback_days: 7        # Analysis window
  min_confidence: 0.7     # Suggestion threshold
---
```

## Data Storage

| Data | Location |
|------|----------|
| Events | `~/.claude/auto-skill/events.db` |
| Skills | `~/.claude/skills/auto/` |
| Registry | `references/registry.json` |

## Privacy

- All data is stored locally
- No data is sent to external services
- Events can be cleaned up with `cleanup_old_events(days=30)`

## Troubleshooting

**No patterns detected?**
- Need 3+ occurrences of the same sequence
- Check the lookback period (default: 7 days)
- Run `/auto-skill:status` to see event counts

**Skill not loading?**
- Run `python scripts/skill_registry.py --rebuild`
- Check the skill exists in `~/.claude/skills/auto/`

**Hooks not working?**
- Verify plugin is installed correctly
- Check `hooks/hooks.json` configuration
- Ensure Python 3 is available

**Want to reset?**
- Delete `~/.claude/auto-skill/events.db`
- Remove skills from `~/.claude/skills/auto/`
