---
sidebar_position: 1
---

# Installation

## Prerequisites

- Python 3.9+
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and working

## Install

Clone the repository:

```bash
git clone https://github.com/MaTriXy/claude-auto-skill.git
cd claude-auto-skill
```

Install dependencies:

```bash
pip install -e .
```

This installs the core dependency (PyYAML) and registers the CLI entry points.

### Optional: V2 Features

For code structure analysis and enhanced pattern detection:

```bash
pip install -e ".[v2]"
```

This adds:
- **pygls** — Language Server Protocol support
- **tree-sitter** + language parsers — Multi-language AST analysis
- **numpy** + **scikit-learn** — ML-based confidence scoring

### Optional: Web UI

```bash
pip install -r web/requirements.txt
```

## Initialize

Run the init command to set up directories and databases:

```bash
python -m commands.init
```

This creates:
- `~/.claude/auto-skill/` — Event database and config
- `~/.claude/skills/auto/` — Auto-generated skill output directory
- `~/.claude/auto-skill.local.md` — Default configuration

## Register Hooks

Auto-Skill integrates with Claude Code through its [hook system](https://docs.anthropic.com/en/docs/claude-code/hooks). The hooks are defined in `hooks/hooks.json`:

```json
{
  "hooks": [
    {
      "type": "PostToolUse",
      "command": "python3 observer.py record",
      "description": "Record tool usage events"
    },
    {
      "type": "Stop",
      "command": "python3 observer.py analyze",
      "description": "Analyze patterns when Claude stops"
    }
  ]
}
```

Copy or merge this into your Claude Code hooks configuration to start observing.

## Verify

Check that everything is set up:

```bash
python -m commands.discover --stats
```

You should see an empty stats output (no patterns detected yet). As you use Claude Code with the hooks active, patterns will start accumulating.
