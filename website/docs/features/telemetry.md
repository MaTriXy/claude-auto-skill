---
sidebar_position: 5
---

# Telemetry

Auto-Skill includes privacy-first anonymous telemetry following the principles from the [anonymous-telemetry](https://github.com/MaTriXy/agent-registry/blob/main/agents/anonymous-telemetry.md) agent specification.

## Architecture

Telemetry operates on two layers:

1. **Local** — SQLite database at `~/.claude/auto-skill/telemetry.db` for effectiveness reports and event history
2. **Remote** — Fire-and-forget HTTP to `t.insightx.pro` for anonymous aggregate reporting (forwarded to Firebase GA4)

## What We Collect

Anonymous, aggregate metrics only:

| Data | Example | Purpose |
|------|---------|---------|
| Event type | `skill_used`, `search` | Feature usage |
| Result counts | `5 results` | Effectiveness |
| Timing | `45ms` | Performance |
| Outcome | `success` / `failure` | Reliability |
| Agent name | `claude-code` | Compatibility |
| System info | `darwin`, `python 3.12` | Compatibility |
| Tool version | `3.0.0` | Adoption |

## What We Do NOT Collect

- No search queries
- No file names or paths
- No session IDs
- No skill content
- No IP addresses
- No personal information

## Disable Telemetry

```bash
# Tool-specific
export AUTO_SKILL_NO_TELEMETRY=1

# Universal standard
export DO_NOT_TRACK=1
```

Add to `~/.bashrc` or `~/.zshrc` to disable permanently.

## Automatic Opt-Out

Telemetry is automatically disabled in CI environments:
GitHub Actions, GitLab CI, CircleCI, Travis CI, Buildkite, Jenkins.

## Implementation

- Fire-and-forget daemon threads (never blocks user workflow)
- Silent failures (telemetry errors never surface to users)
- 2-second HTTP timeout
- Source: [`core/telemetry.py`](https://github.com/MaTriXy/claude-auto-skill/blob/main/core/telemetry.py)

## Local Queries

```bash
auto-skill telemetry report    # Aggregated effectiveness per skill
auto-skill telemetry events    # Raw event log
```
