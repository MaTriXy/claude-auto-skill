---
sidebar_position: 1
---

# Architecture

Auto-Skill follows a three-stage pipeline: **Observe → Detect → Forge**, with an optional discovery layer for community skills.

```
┌─────────────────────────────────────────────────────┐
│                  Claude Code Session                 │
│  User works normally → tool calls happen             │
└──────────────────────┬──────────────────────────────┘
                       │ PostToolUse hook
                       ▼
┌──────────────────────────────────────────────────────┐
│  OBSERVER (hooks/observer.py)                        │
│  Records tool events to SQLite                       │
│  Fields: tool_name, input, response, success, time   │
└──────────────────────┬───────────────────────────────┘
                       │ Stop hook
                       ▼
┌──────────────────────────────────────────────────────┐
│  DETECTOR (core/pattern_detector.py)                 │
│                                                      │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │ Sequence    │ │ Session      │ │ Design       │  │
│  │ Matcher     │ │ Analyzer     │ │ Pattern      │  │
│  │ (V1 core)   │ │ (V2 context) │ │ Detector     │  │
│  └──────┬──────┘ └──────┬───────┘ └──────┬───────┘  │
│         └───────────────┼────────────────┘           │
│                         ▼                            │
│              Confidence Scoring                      │
│     (occurrences × success × length × recency)      │
└──────────────────────┬───────────────────────────────┘
                       │ patterns with confidence ≥ 0.7
                       ▼
┌──────────────────────────────────────────────────────┐
│  FORGE (core/skill_generator.py)                     │
│  Generates SKILL.md with YAML frontmatter            │
│  Output: ~/.claude/skills/auto/                      │
└──────────────────────────────────────────────────────┘
```

## Core Modules

| Module | File | Purpose |
|--------|------|---------|
| **EventStore** | `core/event_store.py` | SQLite persistence for tool events |
| **PatternDetector** | `core/pattern_detector.py` | Core pattern matching + V2 orchestration |
| **SequenceMatcher** | `core/sequence_matcher.py` | Sliding-window subsequence extraction |
| **SkillGenerator** | `core/skill_generator.py` | SKILL.md file generation |
| **SessionAnalyzer** | `core/session_analyzer.py` | Conversation intent and context |
| **LSPAnalyzer** | `core/lsp_analyzer.py` | Code structure via AST/tree-sitter |
| **DesignPatternDetector** | `core/design_pattern_detector.py` | 18 pattern recognizers |
| **Config** | `core/config.py` | Configuration management |

## Hybrid Layer (Optional)

When enabled, the pipeline extends with external sources:

```
┌──────────────────────────────────────────────────────┐
│  UNIFIED SUGGESTER (core/unified_suggester.py)       │
│                                                      │
│  Sources:                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐ │
│  │ Local    │ │ Mental   │ │ Skills.sh            │ │
│  │ Patterns │ │ Model    │ │ (27k+ community)     │ │
│  └────┬─────┘ └────┬─────┘ └────────┬─────────────┘ │
│       └─────────────┼────────────────┘               │
│                     ▼                                │
│     Ranking: local > proven > hints > external       │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  ADOPTION & GRADUATION                               │
│  core/skill_tracker.py + core/graduation_manager.py  │
│                                                      │
│  External skill (50%) → Proven (75%) → Local (85%+)  │
│  Criteria: 5+ uses, 80% success rate                 │
└──────────────────────────────────────────────────────┘
```

## Storage

All data is local. No telemetry is sent anywhere.

| Store | Location | Format |
|-------|----------|--------|
| Tool events | `~/.claude/auto-skill/events.db` | SQLite |
| Adoption tracking | `~/.claude/auto-skill/skills_tracking.db` | SQLite |
| Generated skills | `~/.claude/skills/auto/` | SKILL.md files |
| External skills | `~/.claude/skills/external/` | SKILL.md files |
| Graduation log | `skills/graduation_log.json` | JSON |

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.9+ |
| Storage | SQLite (built-in) |
| Code parsing | AST (Python), tree-sitter (JS/TS) |
| Config format | YAML |
| Skill format | Markdown + YAML frontmatter |
| Web UI | Flask |
| ML (optional) | scikit-learn, numpy |
