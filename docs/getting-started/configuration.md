# Configuration

Customize Claude Auto-Skill behavior via `~/.claude/auto-skill.local.md`.

## Configuration File

The config file is created automatically by `python -m commands.init`:

```yaml
---
detection:
  min_occurrences: 3       # Pattern threshold
  min_sequence_length: 2   # Min tool calls in pattern
  max_sequence_length: 10  # Max tool calls in pattern
  lookback_days: 7         # History window
  min_confidence: 0.7      # Confidence threshold

hybrid:
  enable_mental: true      # Mental Model integration
  enable_external: true    # Skills.sh discovery
  auto_graduate: true      # Auto-graduation

v2:
  enable_session_analysis: true
  enable_lsp_analysis: true
  enable_pattern_detection: true
---
```

## Options

### Detection Settings

- `min_occurrences`: Minimum times a pattern must appear (default: 3)
- `min_sequence_length`: Minimum tools in sequence (default: 2)
- `max_sequence_length`: Maximum tools in sequence (default: 10)
- `lookback_days`: How many days to look back (default: 7)
- `min_confidence`: Minimum confidence to generate skill (default: 0.7)

### Hybrid Settings

- `enable_mental`: Enable Mental Model integration
- `enable_external`: Enable Skills.sh external discovery
- `auto_graduate`: Automatically graduate eligible skills

### V2 Settings

- `enable_session_analysis`: Enable intent/workflow detection
- `enable_lsp_analysis`: Enable code structure analysis
- `enable_pattern_detection`: Enable design pattern detection

## Examples

### More Sensitive Detection

```yaml
detection:
  min_occurrences: 2  # Lower threshold
  min_confidence: 0.6
```

### Local-Only (No External)

```yaml
hybrid:
  enable_mental: false
  enable_external: false
```

### Custom Paths

```yaml
paths:
  events_db: /custom/path/events.db
  skills_dir: /custom/path/skills
  tracker_db: /custom/path/tracker.db
```

## Next Steps

- [Quick Start](quick-start.md)
- [CLI Commands](../guide/cli-commands.md)
