---
sidebar_position: 2
---

# Quick Start

Once you've [installed](/getting-started/installation) Auto-Skill and registered the hooks, here's what happens.

## 1. Work Normally

Use your coding agent as you always do. The observer hook silently records tool events (which tools were called, inputs, outcomes) into a local SQLite database.

Every tool call generates an event like:

```python
ToolEvent(
    tool_name="Read",
    tool_input={"file_path": "src/auth.py"},
    success=True,
    session_id="abc123",
    project_path="/my-project"
)
```

## 2. Patterns Emerge

After a few sessions, the detector looks for repeated tool sequences. For example, if you consistently:

1. **Read** a file
2. **Edit** it
3. **Bash** to run tests
4. **Bash** to check output

...and this happens 3+ times across sessions, it becomes a pattern candidate.

## 3. Review Suggestions

Discover detected patterns:

```bash
python -m commands.discover
```

Output:

```
Detected Patterns:
  1. read-edit-test-verify (confidence: 0.82, occurrences: 5)
  2. debug-read-grep-fix  (confidence: 0.74, occurrences: 3)
```

## 4. Generate Skills

Patterns above the confidence threshold (default: 0.7) can be turned into SKILL.md files. The generated skill includes:

- YAML frontmatter with metadata and confidence scores
- Step-by-step workflow description
- Session context (intent, workflow type)
- Design patterns detected in your code

## 5. Discover Community Skills

Search Skills.sh for existing skills that match your workflow:

```bash
python -m commands.discover --search "testing workflow"
```

External skills start at 50% confidence and graduate to local skills after proving themselves (5+ uses, 80% success rate).

## 6. Web Dashboard (Optional)

Launch the web UI to visualize patterns and manage skills:

```bash
cd web
python app.py
# Open http://localhost:8000
```

## What's Next

- [Configuration](/getting-started/configuration) — Tune detection thresholds and enable features
- [How It Works](/how-it-works/architecture) — Understand the pipeline architecture
- [Pattern Detection](/how-it-works/pattern-detection) — Deep dive into how patterns are found
