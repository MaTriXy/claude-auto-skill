# Claude Auto-Skill

**Automatically learn from your workflows and turn them into reusable skills.**

Claude Auto-Skill observes your Claude Code sessions, detects repeated tool patterns, and generates reusable skills. Skills can be loaded dynamically mid-session without restarting.

## What It Does

```
Session 1: Grep → Read → Edit    ─┐
Session 2: Grep → Read → Edit     ├──▶  Pattern Detected!
Session 3: Grep → Read → Edit    ─┘          │
                                             ▼
                                    "search-and-edit-workflow"
                                    (85% confidence)
                                             │
                                             ▼
                                    ~/.claude/skills/auto/
```

## Key Features

| Feature | Description |
|---------|-------------|
| **Auto-Detection** | Recognizes repeated tool sequences across sessions |
| **Dynamic Loading** | Load skills mid-session without restart |
| **Proactive Discovery** | Claude offers relevant skills automatically |
| **Execution Context** | Skills can run inline or in isolated subagents |
| **Tool Restrictions** | Generated skills only use their detected tools |

## Quick Start

### Installation

```bash
# Clone to plugins directory
git clone https://github.com/MaTriXy/claude-auto-skill ~/.claude/plugins/auto-skill

# Install dependencies
pip install pyyaml
```

### Usage

Once installed, the plugin automatically:
1. Records your tool usage patterns
2. Detects repeated workflows
3. Offers to create skills from high-confidence patterns

### Commands

```bash
/auto-skill:review              # List detected patterns
/auto-skill:review approve ID   # Create skill from pattern
/auto-skill:load <name>         # Load a skill mid-session
/auto-skill:status              # Show system stats
```

---

## How It Works

### The Learning Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           OBSERVATION PHASE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   PostToolUse Hook                                                       │
│        │                                                                 │
│        ▼                                                                 │
│   ┌─────────────────┐                                                    │
│   │   EventStore    │  Records: tool_name, inputs, response, success    │
│   │    (SQLite)     │  Tagged with: session_id, project_path, timestamp │
│   └─────────────────┘                                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           DETECTION PHASE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────────────┐     ┌───────────────────┐                        │
│   │ SequenceMatcher  │────▶│  PatternDetector  │                        │
│   │                  │     │                   │                        │
│   │ Finds repeated   │     │ Scores patterns:  │                        │
│   │ subsequences     │     │ • Occurrences 40% │                        │
│   │ across sessions  │     │ • Length 20%      │                        │
│   └──────────────────┘     │ • Success 25%     │                        │
│                            │ • Recency 15%     │                        │
│                            └───────────────────┘                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           GENERATION PHASE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────────────┐     ┌───────────────────┐     ┌───────────────┐  │
│   │  User Approval   │────▶│  SkillGenerator   │────▶│   SKILL.md    │  │
│   │                  │     │                   │     │               │  │
│   │ Review & confirm │     │ • Name & desc     │     │ Saved to:     │  │
│   │ pattern matches  │     │ • context: fork   │     │ ~/.claude/    │  │
│   │ your intent      │     │ • allowed-tools   │     │ skills/auto/  │  │
│   └──────────────────┘     └───────────────────┘     └───────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Dynamic Skill Loading

Unlike standard Claude Code skills (loaded at session start), auto-generated skills can be loaded **mid-session**:

```
┌─────────────────────────────────────────────────────────────────┐
│ User: "Find all TODO comments and fix them"                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Claude invokes skill-discovery automatically                    │
│                                                                 │
│ $ python scripts/discover_skill.py "find TODO fix"              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ ## Skill Discovery                                              │
│                                                                 │
│ I found an auto-generated skill that matches your task:         │
│                                                                 │
│ **search-and-fix-workflow** (confidence: 85%)                   │
│ > Search for issues in codebase and fix them systematically     │
│                                                                 │
│ - Runs in: Current context (inline)                             │
│ - Tools: Grep, Read, Edit                                       │
│                                                                 │
│ **Would you like me to load this skill?**                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                       User: "Yes"
                              │
                              ▼
┌─════════════════════════════════════════════════════════════════┐
│ SKILL LOADED: search-and-fix-workflow                           │
│ Confidence: 85%                                                 │
│ Allowed tools: Grep, Read, Edit                                 │
│═════════════════════════════════════════════════════════════════│
│                                                                 │
│ ## Steps                                                        │
│ 1. Search - Use Grep to find relevant patterns                  │
│ 2. Read - Read matching files to understand context             │
│ 3. Fix - Edit the files to resolve issues                       │
│ 4. Verify - Confirm the fix is correct                          │
│                                                                 │
│═════════════════════════════════════════════════════════════════│
│ END OF SKILL - INSTRUCTIONS ARE NOW ACTIVE                      │
└─════════════════════════════════════════════════════════════════┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Claude follows the loaded instructions to complete the task     │
└─────────────────────────────────────────────────────────────────┘
```

### Execution Contexts

Generated skills automatically get appropriate execution settings based on their tools:

| Pattern Type | Context | Agent | Why |
|-------------|---------|-------|-----|
| `Grep → Read → Glob` | Inline | Explore | Read-only, safe in current context |
| `Read → Edit → Bash` | Fork | general-purpose | Has side effects, needs isolation |
| `Read → Task` | Fork | general-purpose | Spawns subagents, needs isolation |

**Inline**: Skill runs in current conversation context. Good for reference and guidelines.

**Fork**: Skill runs in isolated subagent. Good for tasks with side effects that shouldn't pollute conversation history.

---

## Pattern Detection

### What Gets Detected

Patterns are detected when:
- Same tool sequence appears **3+ times** across sessions
- Sequence is **2-10 tools** long
- Pattern occurred within the **last 7 days**

### Confidence Scoring

| Factor | Weight | Description |
|--------|--------|-------------|
| Occurrences | 40% | Logarithmic scale, more = higher |
| Length | 20% | 3-5 tools is ideal range |
| Success Rate | 25% | Patterns that succeed score higher |
| Recency | 15% | Recent patterns prioritized |

### Example Patterns

```
Grep → Read → Edit         # Search, understand, modify
Glob → Read → Write        # Find files, read, create new
Read → Edit → Bash         # Read, modify, run tests
Grep → Read → Glob → Edit  # Complex search and edit workflow
```

---

## Generated Skills

Auto-generated skills are saved to `~/.claude/skills/auto/` with:

```yaml
---
name: search-and-edit-workflow-a1b2c3
description: Workflow that searches then edits
context: fork                    # Runs in isolated subagent
agent: general-purpose           # Which agent type to use
allowed-tools: Grep, Read, Edit  # Tool restrictions
auto-generated: true
confidence: 0.85
pattern-id: a1b2c3
---

# search-and-edit-workflow-a1b2c3

Workflow: search -> read -> edit

## Steps

1. Search for the relevant patterns in the codebase
2. Read the relevant file(s) to understand the current state
3. Make the necessary edits to the file
```

---

## Configuration

Create `~/.claude/auto-skill.local.md` to customize:

```yaml
---
detection:
  min_occurrences: 3        # Minimum pattern repetitions
  min_sequence_length: 2    # Shortest pattern to detect
  max_sequence_length: 10   # Longest pattern to detect
  lookback_days: 7          # Analysis window
  min_confidence: 0.7       # Threshold for suggestions
  ignored_tools:            # Tools to exclude
    - AskUserQuestion
enabled: true
---
```

---

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
│   ├── sequence_matcher.py      # Subsequence matching algorithm
│   ├── skill_generator.py       # SKILL.md generation
│   └── config.py                # Configuration management
├── scripts/
│   ├── skill_registry.py        # Skill index management
│   ├── get_skill.py             # Load specific skill
│   ├── search_skills.py         # Search by intent
│   ├── list_skills.py           # List all skills
│   └── discover_skill.py        # Combined discovery + loading
├── commands/
│   ├── review-patterns.md       # /auto-skill:review
│   ├── status.md                # /auto-skill:status
│   └── load-skill.md            # /auto-skill:load
├── skills/
│   ├── SKILL.md                 # Plugin documentation
│   └── skill-discovery/         # Auto-discovery skill
│       └── SKILL.md
└── tests/
    └── test_*.py                # Unit tests (35 tests)
```

---

## Data Storage

| Data | Location | Description |
|------|----------|-------------|
| Events | `~/.claude/auto-skill/events.db` | SQLite database of tool calls |
| Skills | `~/.claude/skills/auto/` | Generated SKILL.md files |
| Registry | `references/registry.json` | Lightweight skill index |

### Privacy

- All data is stored **locally** on your machine
- No data is sent to external services
- Old events are cleaned up after 30 days

---

## Development

### Run Tests

```bash
cd ~/.claude/plugins/auto-skill
pytest tests/ -v
```

### Rebuild Skill Registry

```bash
python scripts/skill_registry.py --rebuild
```

### Manual Skill Operations

```bash
# List all skills
python scripts/list_skills.py --verbose

# Search for skills
python scripts/search_skills.py "search and edit"

# Load a specific skill
python scripts/get_skill.py <skill-name>

# Discover and offer skills
python scripts/discover_skill.py "your task description"
```

---

## Credits

- Inspired by the [Agent Registry](https://github.com/MaTriXy/Agent-Registry) lazy-loading pattern
- Built for [Claude Code](https://claude.ai/code)

## License

MIT
