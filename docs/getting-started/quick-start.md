# Quick Start

Generate your first skill in 5 minutes! ⚡

## Overview

This guide walks you through:

1. ✅ Setting up Claude Auto-Skill
2. ✅ Running pattern detection
3. ✅ Generating your first skill
4. ✅ Using the Web UI

**Time**: ~5 minutes

---

## Step 1: Install

```bash
# Clone and install
git clone https://github.com/MaTriXy/claude-auto-skill.git
cd claude-auto-skill
pip install -r requirements.txt

# Initialize
python -m commands.init
```

✅ **Checkpoint**: You should see:

```
✨ Claude Auto-Skill Initialized

Created directories:
  ~/.claude/auto-skill/
  ~/.claude/skills/auto/

Created config:
  ~/.claude/auto-skill/auto-skill.local.md

Next steps:
  1. Use Claude Code normally
  2. Run: python run_detector.py
  3. Check ~/.claude/skills/auto/
```

---

## Step 2: Work Normally

Use Claude Code as usual. Auto-Skill watches in the background.

**Example Session** (create a simple script):

```python
# 1. Read existing file
cat example.py

# 2. Edit with improvements
# (make changes)

# 3. Run tests
pytest test_example.py

# 4. Edit again if needed
# (fix issues)
```

This creates an **event sequence**: `read → edit → bash → edit`

---

## Step 3: Detect Patterns

After a few sessions, run pattern detection:

```bash
python run_detector.py
```

**Output**:

```
🔍 Analyzing sessions...

Found 3 patterns:

1. read-edit-test-edit (TDD Workflow)
   Confidence: 85%
   Occurrences: 5
   
2. read-search-edit (Code Navigation)
   Confidence: 78%
   Occurrences: 4

3. read-bash-edit (Debug Fix)
   Confidence: 82%
   Occurrences: 6

✅ Generated 3 skills → ~/.claude/skills/auto/
```

---

## Step 4: View Generated Skills

Check your generated skills:

```bash
ls ~/.claude/skills/auto/
# Output:
# read-edit-test-edit-abc123.md
# read-search-edit-def456.md
# read-bash-edit-ghi789.md

# View a skill
cat ~/.claude/skills/auto/read-edit-test-edit-abc123.md
```

**Example Skill**:

```yaml
---
name: read-edit-test-edit-abc123
confidence: 0.85

# V2 metadata
session-analysis:
  primary_intent: implement
  workflow_type: TDD

# Vercel compatibility
compatible-agents: [claude-code, opencode, codex]
tags: [read, edit, test, implement, tdd]
---

# TDD Workflow

**Pattern**: read → edit → bash:pytest → edit

## When to Use

Use this skill when:
- Implementing new features with TDD
- Adding tests before code
- Iterating on test failures

## Detected Pattern

Tool sequence:
1. read: Review existing code
2. edit: Implement feature
3. bash: Run pytest
4. edit: Fix failures

## Success Indicators

- Tests pass
- No syntax errors
- Feature complete
```

---

## Step 5: Start Web UI

Launch the visual interface:

```bash
cd web
pip install -r requirements.txt
python app.py
```

Open browser: [http://localhost:5000](http://localhost:5000)

**Dashboard** shows:

- 📊 Total skills: 3
- 🏠 Local skills: 3
- 🌐 External skills: 0
- 📈 Usage stats
- ✨ Confidence levels

---

## Step 6: Browse Skills

In the Web UI:

1. **Search**: Type "tdd" in search box
2. **Filter**: Click a skill card
3. **View Details**: See confidence, usage, success rate

**Skill Card** displays:

```
┌─────────────────────────────┐
│ read-edit-test-edit         │
│ [local] 5 uses • 100% success│
│ ▓▓▓▓▓▓▓▓▓░ 85%             │
└─────────────────────────────┘
```

---

## Step 7: Discover External Skills

Search skills.sh for community skills:

```bash
python -m commands.discover --search "payment"
```

**Output**:

```
🌐 External Skills (skills.sh)

1. stripe-integration (4.5★, 342 installs)
   Stripe payment processing with error handling
   
2. payment-retry-logic (4.2★, 128 installs)
   Automatic retry for failed payments
   
3. fraud-detection (4.7★, 89 installs)
   ML-based payment fraud detection
```

---

## Step 8: Adopt External Skill

Use an external skill and track adoption:

```python
from core.skill_tracker import SkillTracker

tracker = SkillTracker('~/.claude/auto-skill/skill_tracker.db')

# Record usage
tracker.record_adoption(
    skill_name='stripe-integration',
    source='external',
    success=True
)

# Check confidence
stats = tracker.get_skill_stats('stripe-integration')
print(f"Confidence: {stats['confidence']:.0%}")
# Output: Confidence: 50%  (external, unproven)
```

After 5 successful uses:

```python
stats = tracker.get_skill_stats('stripe-integration')
print(f"Confidence: {stats['confidence']:.0%}")
# Output: Confidence: 85%  (ready for graduation!)
```

---

## Step 9: Graduate External Skill

When external skills prove valuable, graduate them to local:

```bash
python -m core.graduation_manager
```

**Output**:

```
🎓 Found 1 graduation candidate:

1. stripe-integration
   Confidence: 88% | Usage: 8 | Success: 87%

🎓 Graduation Candidate: stripe-integration
   Confidence: 88%
   Usage: 8 times (87% success)
   Source: external
   Author: community

Graduate this skill to local? [Y/n]: y

✅ Graduated: stripe-integration
   Saved to: ~/.claude/skills/auto/stripe-integration.md
   New confidence: 80% (local)
```

---

## Step 10: Publish Your Skills

Share your best skills with the community:

```bash
# Detect publishable skills
python -m core.skillssh_publisher detect

# Output:
# 📦 Found 2 publishable skills:
#   - tdd-workflow
#   - debug-fix-pattern

# Publish
python -m core.skillssh_publisher publish tdd-workflow

# Output:
# ✅ Published: tdd-workflow
#    URL: https://skills.sh/skill/tdd-workflow
```

---

## Next Steps

Congratulations! You've:

✅ Installed Claude Auto-Skill  
✅ Generated skills from your patterns  
✅ Used the Web UI  
✅ Discovered external skills  
✅ Graduated a skill  
✅ Published to the community

### Where to Go from Here

<div class="grid cards" markdown>

-   :material-cog: **[Configuration](configuration.md)**

    Customize detection thresholds and behavior

-   :material-brain: **[Mental Model Integration](../features/mental-model.md)**

    Add domain-aware context to your skills

-   :material-book: **[CLI Commands](../guide/cli-commands.md)**

    Complete command reference

-   :material-web: **[Web UI Guide](../features/web-ui.md)**

    Master the visual interface

</div>

---

## Common Workflows

### Daily Development

```bash
# Morning: Check yesterday's patterns
python run_detector.py

# Work normally with Claude Code
# ...

# Evening: Review new skills
ls ~/.claude/skills/auto/

# Weekly: Check graduation candidates
python -m core.graduation_manager stats
```

### Team Collaboration

```bash
# 1. Setup Mental Model
cd your-project
mental init
mental add domain "Payment"
mental add capability "Checkout"

# 2. Generate team skills
python run_detector.py

# 3. Commit skills to repo
cd ~/.claude/skills
git init
git add auto/
git commit -m "Add team skills"
git push
```

### Open Source Contribution

```bash
# 1. Detect publishable skills
python -m core.skillssh_publisher detect

# 2. Publish to skills.sh
python -m core.skillssh_publisher publish skill-name

# 3. Track community adoption
python -m core.skillssh_publisher sync
python -m core.skillssh_publisher stats
```

---

## Tips & Tricks

### ⚡ Speed Up Detection

Lower thresholds in config:

```yaml
detection:
  min_occurrences: 2  # Instead of 3
```

### 🎯 Focus on Specific Patterns

Use `.autoignore`:

```
# Ignore read-only patterns
read,read,read

# Focus on TDD
!*test*
```

### 📊 Track Progress

```bash
# Daily stats
python -m commands.discover --stats

# Confidence trends
python -c "from core.skill_tracker import SkillTracker; \
  tracker = SkillTracker('~/.claude/auto-skill/skill_tracker.db'); \
  print(tracker.get_all_stats())"
```

### 🔄 Auto-Graduate

Enable in config:

```yaml
hybrid:
  auto_graduate: true
```

Then run periodically:

```bash
# Cron job (daily at 6pm)
0 18 * * * cd ~/claude-auto-skill && python -m core.graduation_manager auto 5
```

---

## Troubleshooting Quick Start

### No Patterns Detected

**Problem**: `python run_detector.py` finds 0 patterns

**Solutions**:

1. **Use Claude Code more**: Need 3+ sessions
2. **Lower threshold**:
   ```yaml
   detection:
     min_occurrences: 2
   ```
3. **Check events**:
   ```python
   from core.event_store import EventStore
   store = EventStore('~/.claude/auto-skill/events.db')
   print(store.get_recent_events(10))
   ```

### Web UI Won't Start

**Problem**: `python app.py` fails

**Solutions**:

1. **Install Flask**:
   ```bash
   cd web
   pip install -r requirements.txt
   ```
2. **Check port**:
   ```bash
   lsof -i :5000  # Port in use?
   python app.py --port 8080  # Try different port
   ```

### Skills Not Loading

**Problem**: Web UI shows 0 skills

**Solutions**:

1. **Check database**:
   ```bash
   ls ~/.claude/auto-skill/
   # Should show: events.db, skill_tracker.db
   ```
2. **Reinitialize**:
   ```bash
   python -m commands.init --force
   ```

---

## Ready for More?

You're all set! Explore advanced features:

- [Mental Model Integration](../features/mental-model.md)
- [Design Pattern Detection](../features/pattern-detection.md)
- [Graduation System](../features/graduation.md)
- [Publishing Guide](../features/publishing.md)

---

**Need help?** [Open an issue](https://github.com/MaTriXy/claude-auto-skill/issues) or check the [FAQ](../faq.md)
