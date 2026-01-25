---
name: review-patterns
description: Review detected workflow patterns and approve skill generation
arguments:
  - name: action
    description: "Action to perform: list, approve, reject, preview"
    required: false
    default: list
  - name: pattern-id
    description: "Pattern ID to act on (for approve/reject/preview)"
    required: false
---

# Auto-Skill Pattern Review

Review and approve automatically detected workflow patterns for skill generation.

## Instructions

When invoked, analyze the user's intent and perform the appropriate action:

### List Patterns (default)

If no arguments or `action=list`:

1. Import and use the pattern detection system:
   ```python
   import sys
   sys.path.insert(0, "$CLAUDE_PROJECT_ROOT")
   from core.event_store import EventStore
   from core.pattern_detector import PatternDetector

   store = EventStore()
   detector = PatternDetector(store)
   patterns = detector.get_pending_patterns(min_confidence=0.6)
   ```

2. Display detected patterns in a clear format:
   - Pattern ID (first 8 characters)
   - Tool sequence
   - Occurrence count
   - Confidence score (as percentage)
   - Suggested name

3. Explain available actions:
   - `/auto-skill:review approve <pattern-id>` - Generate skill from pattern
   - `/auto-skill:review reject <pattern-id>` - Dismiss pattern
   - `/auto-skill:review preview <pattern-id>` - Show skill preview

### Preview Pattern

If `action=preview` with a pattern-id:

1. Load the specific pattern by ID
2. Generate a skill candidate (without saving)
3. Display the full SKILL.md content that would be created
4. Ask user if they want to approve or customize

### Approve Pattern

If `action=approve` with a pattern-id:

1. Load the specific pattern
2. Generate the skill candidate
3. **Ask the user** if they want to:
   - Use the auto-generated name or provide a custom name
   - Use the auto-generated description or customize it
   - Add any additional notes or steps
4. Save the skill to `~/.claude/skills/auto/<skill-name>/SKILL.md`
5. Confirm creation and show the path

### Reject Pattern

If `action=reject` with a pattern-id:

1. Mark the pattern as rejected (store in a blacklist)
2. Confirm the pattern will not be suggested again

## Example Output for List

```
## Detected Workflow Patterns

| ID       | Pattern                    | Count | Confidence |
|----------|----------------------------|-------|------------|
| a1b2c3d4 | Grep -> Read -> Edit      | 5     | 85%        |
| e5f6g7h8 | Glob -> Read -> Write     | 3     | 72%        |

Commands:
- `/auto-skill:review preview a1b2c3d4` - Preview skill
- `/auto-skill:review approve a1b2c3d4` - Generate skill
```

## Notes

- Only patterns with confidence >= 60% are shown by default
- Approved skills are saved to `~/.claude/skills/auto/`
- Auto-generated skills include metadata for tracking their origin
- Users can always edit generated skills after creation
