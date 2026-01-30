---
sidebar_position: 1
---

# Installation

## Prerequisites

- At least one supported coding agent installed (Claude Code, Cursor, Codex, Aider, Windsurf, Cline, Amp, Continue, OpenCode, or GitHub Copilot)

## Install

```bash
npx skills add MaTriXy/auto-skill
```

This uses the [Skills CLI](https://github.com/vercel-labs/skills) to install Auto-Skill directly into your coding agent. It auto-detects installed agents (Claude Code, Cursor, Codex, etc.) and sets up skills for you.

You can also select specific skills during install:

```bash
npx skills add MaTriXy/auto-skill -s auto-skill-guide
npx skills add MaTriXy/auto-skill -s skill-discovery
```

## Initialize

Run the init command to set up directories and databases:

```bash
auto-skill init
```

This creates:
- `~/.claude/auto-skill/` — Event database and config
- `~/.claude/skills/auto/` — Auto-generated skill output directory
- `~/.claude/auto-skill.local.md` — Default configuration

## Register Hooks

Auto-Skill integrates with coding agents through hook systems. For Claude Code, it uses the [hook system](https://docs.anthropic.com/en/docs/claude-code/hooks). The hooks are defined in `hooks/hooks.json`:

```json
{
  "hooks": [
    {
      "type": "PostToolUse",
      "command": "node observer.js record",
      "description": "Record tool usage events"
    },
    {
      "type": "Stop",
      "command": "node observer.js analyze",
      "description": "Analyze patterns when Claude stops"
    }
  ]
}
```

Copy or merge this into your agent's hooks configuration to start observing.

## Verify

Check that everything is set up:

```bash
auto-skill version
auto-skill stats
```

You should see an empty stats output (no patterns detected yet). As you use your coding agent with the hooks active, patterns will start accumulating.
