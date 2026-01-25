# Claude Auto-Skill

Automatically detect workflow patterns and generate Claude Code skills.

## Overview

Claude Auto-Skill observes your Claude Code sessions, detects repeated tool patterns, and suggests reusable skills. When you approve a pattern, it generates a SKILL.md file that Claude can use in future sessions.

## How It Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PostToolUse   │────▶│   EventStore    │────▶│ PatternDetector │
│      Hook       │     │    (SQLite)     │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    SKILL.md     │◀────│ SkillGenerator  │◀────│  User Approval  │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

1. **Observe**: Every tool call is recorded via PostToolUse hook
2. **Detect**: When sessions end, patterns are analyzed for repetition
3. **Suggest**: High-confidence patterns are suggested as skill candidates
4. **Generate**: Approved patterns become SKILL.md files

## Installation

1. Clone this repository to your plugins directory:
   ```bash
   git clone https://github.com/anthropics/claude-auto-skill ~/.claude/plugins/auto-skill
   ```

2. Install Python dependencies:
   ```bash
   pip install -r ~/.claude/plugins/auto-skill/requirements.txt
   ```

3. The plugin hooks will activate automatically in Claude Code.

## Usage

### Review Detected Patterns

```
/auto-skill:review              # List all detected patterns
/auto-skill:review preview ID   # Preview a pattern as a skill
/auto-skill:review approve ID   # Generate skill from pattern
/auto-skill:review reject ID    # Dismiss a pattern
```

### Check System Status

```
/auto-skill:status              # Show stats, patterns, and config
```

## Pattern Detection

Patterns are detected when:
- Same tool sequence appears **3+ times** across sessions
- Sequence is **2-10 tools** long
- Pattern occurred within the **last 7 days**

### Confidence Scoring

| Factor | Weight | Description |
|--------|--------|-------------|
| Occurrences | 40% | More = higher confidence |
| Length | 20% | 3-5 tools is ideal |
| Success Rate | 25% | Successful patterns score higher |
| Recency | 15% | Recent patterns are prioritized |

## Configuration

Create `~/.claude/auto-skill.local.md` to customize:

```yaml
---
detection:
  min_occurrences: 3
  min_sequence_length: 2
  max_sequence_length: 10
  lookback_days: 7
  min_confidence: 0.7
enabled: true
---
```

## File Structure

```
claude-auto-skill/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── hooks/
│   ├── hooks.json               # Hook configuration
│   └── observer.py              # Event capture and analysis
├── core/
│   ├── event_store.py           # SQLite event storage
│   ├── pattern_detector.py      # Pattern recognition
│   ├── sequence_matcher.py      # Subsequence matching
│   ├── skill_generator.py       # SKILL.md generation
│   └── config.py                # Configuration management
├── commands/
│   ├── review-patterns.md       # /auto-skill:review command
│   └── status.md                # /auto-skill:status command
├── skills/
│   └── SKILL.md                 # Plugin documentation
└── tests/
    └── test_*.py                # Unit tests
```

## Data Storage

- **Events**: `~/.claude/auto-skill/events.db` (SQLite)
- **Generated Skills**: `~/.claude/skills/auto/<skill-name>/SKILL.md`

## Privacy

- All data is stored locally on your machine
- No data is sent to external services
- Old events are automatically cleaned up after 30 days

## Development

Run tests:
```bash
cd ~/.claude/plugins/auto-skill
pytest tests/
```

## License

MIT
