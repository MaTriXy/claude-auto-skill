---
name: status
description: Show Auto-Skill system status and diagnostics
---

# Auto-Skill Status

Display the current status of the Auto-Skill system, including event capture statistics, detected patterns, and configuration.

## Instructions

When invoked, gather and display system diagnostics:

1. **Event Store Statistics**

   ```python
   import sys
   sys.path.insert(0, "$CLAUDE_PROJECT_ROOT")
   from core.event_store import EventStore

   store = EventStore()
   stats = store.get_stats()
   ```

   Display:
   - Total events recorded
   - Unique sessions tracked
   - Unique projects observed
   - Top 5 most used tools

2. **Pattern Detection Status**

   ```python
   from core.pattern_detector import PatternDetector

   detector = PatternDetector(store)
   patterns = detector.detect_patterns()
   ```

   Display:
   - Number of patterns detected
   - Number of high-confidence patterns (>= 70%)
   - Number of pending patterns (not yet converted to skills)

3. **Generated Skills**

   ```python
   from core.skill_generator import SkillGenerator

   generator = SkillGenerator()
   skills = generator.list_generated_skills()
   ```

   Display:
   - Number of auto-generated skills
   - List of skill names

4. **Configuration**

   Display current detection thresholds:
   - Minimum occurrences: 3
   - Minimum sequence length: 2
   - Maximum sequence length: 10
   - Lookback days: 7

5. **Database Location**

   Show the path to the events database:
   `~/.claude/auto-skill/events.db`

## Example Output

```
## Auto-Skill Status

### Event Capture
- Total events: 1,234
- Sessions tracked: 45
- Projects observed: 3

### Top Tools
1. Read (456 calls)
2. Edit (321 calls)
3. Bash (234 calls)

### Pattern Detection
- Patterns detected: 8
- High confidence (>= 70%): 3
- Pending review: 2

### Generated Skills
- Total: 2
  - grep-edit-workflow-a1b2c3
  - read-write-workflow-d4e5f6

### Configuration
- min_occurrences: 3
- min_sequence_length: 2
- max_sequence_length: 10
- lookback_days: 7

### Database
Location: ~/.claude/auto-skill/events.db
Size: 2.4 MB
```

## Troubleshooting

If no events are recorded:
1. Ensure the plugin hooks are installed
2. Check that `hooks/hooks.json` is configured correctly
3. Verify the observer script has execute permissions

If patterns aren't detected:
1. Need at least 3 occurrences of the same sequence
2. Sequences must be 2-10 tools long
3. Check lookback period (default: 7 days)
