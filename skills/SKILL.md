---
name: auto-skill-guide
description: Documentation for the Claude Auto-Skill plugin - automatic workflow pattern detection and skill generation
---

# Claude Auto-Skill Plugin

This plugin automatically detects workflow patterns from your Claude Code sessions and generates reusable skills.

## How It Works

1. **Observation**: Every tool call is recorded (via PostToolUse hook)
2. **Detection**: When a session ends, patterns are analyzed for repetition
3. **Suggestion**: High-confidence patterns are suggested for skill creation
4. **Generation**: Approved patterns become SKILL.md files

## Commands

### /auto-skill:review

Review and approve detected patterns:

```
/auto-skill:review              # List all detected patterns
/auto-skill:review preview ID   # Preview a pattern as a skill
/auto-skill:review approve ID   # Generate skill from pattern
/auto-skill:review reject ID    # Dismiss a pattern
```

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

Confidence is calculated from:
- **Occurrence count** (40%): More occurrences = higher confidence
- **Sequence length** (20%): 3-5 tools is ideal
- **Success rate** (25%): Successful patterns score higher
- **Recency** (15%): Recent patterns are prioritized

### Example Patterns

```
Grep -> Read -> Edit        # Search, read context, make changes
Glob -> Read -> Write       # Find files, read, create new file
Read -> Edit -> Bash        # Read file, edit, run tests
```

## Generated Skills

Auto-generated skills are saved to:
```
~/.claude/skills/auto/<skill-name>/SKILL.md
```

Each skill includes:
- YAML frontmatter with metadata
- `auto-generated: true` flag
- Confidence score and source sessions
- Procedural steps derived from the pattern

## Configuration

Detection thresholds (in `~/.claude/auto-skill.local.md`):

```yaml
min_occurrences: 3      # Minimum pattern repetitions
min_sequence_length: 2  # Shortest pattern
max_sequence_length: 10 # Longest pattern
lookback_days: 7        # Analysis window
```

## Data Storage

Events are stored in SQLite:
```
~/.claude/auto-skill/events.db
```

This database contains:
- Tool call events (name, input, response)
- Session and project metadata
- Timestamps for each event

## Privacy

- All data is stored locally
- No data is sent to external services
- Events can be cleaned up with `cleanup_old_events(days=30)`

## Troubleshooting

**No patterns detected?**
- Need 3+ occurrences of the same sequence
- Check the lookback period (default: 7 days)
- Run `/auto-skill:status` to see event counts

**Hooks not working?**
- Verify plugin is installed correctly
- Check `hooks/hooks.json` configuration
- Ensure Python 3 is available

**Want to reset?**
- Delete `~/.claude/auto-skill/events.db`
- Remove skills from `~/.claude/skills/auto/`
