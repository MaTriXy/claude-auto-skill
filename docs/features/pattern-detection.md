# Pattern Detection

Automatic discovery of repeated workflow patterns from your Claude Code sessions.

## How It Works

1. **Record**: Logs every tool call (read, edit, bash, etc.)
2. **Analyze**: Detects repeated sequences (min 3 occurrences)
3. **Generate**: Creates SKILL.md with instructions
4. **Track**: Monitors success to adjust confidence

## Example Patterns

### TDD Workflow

```
read → edit → bash:pytest → edit
```

Detected as: "TDD Workflow" (85% confidence)

### Debug Fix

```
read → bash:run → read → edit
```

Detected as: "Debug Fix Pattern" (82% confidence)

## Configuration

See [Configuration Guide](../getting-started/configuration.md) for detection settings.

## Next Steps

- [Session Analysis](session-analysis.md)
- [Design Pattern Detection](overview.md)
