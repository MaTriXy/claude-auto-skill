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
   ```typescript
   import { createEventStore } from "../src/core/db";
   import { createPatternDetector } from "../src/core/patternDetector";

   const store = createEventStore();
   const detector = createPatternDetector(store);
   const patterns = detector.getPendingPatterns({ minConfidence: 0.6 });
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
2. Generate the skill candidate using:
   ```typescript
   import { createSkillGenerator } from "../src/core/skillGenerator";
   const generator = createSkillGenerator();
   const candidate = generator.generateCandidate(pattern);
   ```

3. **Show the auto-detected execution context**:
   - `context: fork` - Whether skill runs in isolated subagent
   - `agent` - Which agent type (Explore, Plan, general-purpose)
   - `allowed-tools` - Which tools are permitted

4. **Ask the user** if they want to customize:
   - Use the auto-generated name or provide a custom name
   - Use the auto-generated description or customize it
   - **Execution context**: Run inline or in isolation (fork)
   - **Agent type**: If fork, which agent (Explore, Plan, general-purpose)
   - **Tool restrictions**: Use detected tools only, or allow all tools
   - Add any additional notes or steps

5. Save the skill to `~/.claude/skills/auto/<skill-name>/SKILL.md`
6. Confirm creation and show the path
7. **Inject the skill into the current session** by running:
   ```bash
   auto-skill load "<skill-name>"
   ```
   Display the output directly - this makes the skill immediately active without requiring a session restart. The delimited format signals these are instructions to follow.

### Execution Context Options

When presenting the skill candidate, explain:

- **Inline (default for read-only patterns)**: Skill runs in current conversation context. Good for reference material and guidelines.

- **Fork (default for patterns with Bash/Task)**: Skill runs in isolated subagent. Good for:
  - Tasks with side effects (deployments, builds)
  - Workflows that shouldn't pollute conversation history
  - Long-running operations

- **Agent types** (when fork is enabled):
  - `Explore`: Read-only tools, optimized for codebase exploration
  - `Plan`: Planning and design, no execution
  - `general-purpose`: Full tool access (default)

- **Allowed tools**: Restricts Claude to only use specific tools when the skill is active. Prevents scope creep.

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
