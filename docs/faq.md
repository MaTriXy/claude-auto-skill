# Frequently Asked Questions (FAQ)

## General Questions

### What is Claude Auto-Skill?

Claude Auto-Skill is an intelligent skill management system that automatically learns from your Claude Code workflows and generates reusable skills. It combines local pattern detection, Mental Model integration, and external skill discovery to create a comprehensive skill ecosystem.

### How is this different from Vercel Labs Skills?

| Feature | Claude Auto-Skill | Vercel Labs Skills |
|---------|------------------|-------------------|
| **Approach** | Auto-generates from YOUR patterns | Manual skill discovery |
| **Learning** | Learns from actual work | Passive skill library |
| **Mental Model** | ✅ Domain-aware | ❌ No context |
| **Confidence** | ✅ Evolves 50%→85% | ❌ Static |
| **Graduation** | ✅ Automatic | ❌ Manual |
| **Web UI** | ✅ Full dashboard | ❌ CLI only |

**In short**: Vercel Skills is a package manager for external skills. Auto-Skill learns from YOU and generates personalized skills.

### Do I need Mental CLI to use this?

No! Mental Model integration is **optional**. Auto-Skill works great on its own:

- **Without Mental**: Pattern detection + skills.sh discovery
- **With Mental**: Enhanced with domain/capability context

Enable/disable Mental in config:

```yaml
hybrid:
  enable_mental: true  # Set to false to disable
```

### What AI models are supported?

Claude Auto-Skill works with any AI assistant that uses tool calls:

- ✅ Claude Code (Anthropic)
- ✅ OpenCode (SST)
- ✅ Codex (OpenAI)
- ✅ Windsurf (Codeium)
- ✅ Cursor

The tool event format is universal.

---

## Installation & Setup

### What are the system requirements?

- **Python**: 3.9 or higher
- **OS**: macOS, Linux, Windows
- **RAM**: 512 MB minimum (2 GB recommended)
- **Disk**: 100 MB for core, 500 MB with V2 features

### How do I install it?

Three options:

=== "From Source"

    ```bash
    git clone https://github.com/MaTriXy/claude-auto-skill.git
    cd claude-auto-skill
    pip install -r requirements.txt
    python -m commands.init
    ```

=== "PyPI (Coming Soon)"

    ```bash
    pip install claude-auto-skill
    auto-skill init
    ```

=== "With V2 Features"

    ```bash
    pip install -r requirements.txt
    pip install -r requirements-v2.txt  # LSP + ML features
    ```

### Where are skills stored?

Default locations:

```
~/.claude/
├── auto-skill/
│   ├── events.db           # Event store
│   ├── skill_tracker.db    # Adoption tracking
│   └── auto-skill.local.md # Configuration
└── skills/
    └── auto/               # Generated skills
        ├── skill1.md
        ├── skill2.md
        └── ...
```

You can customize paths in `auto-skill.local.md`.

### Can I use a different directory?

Yes! Configure in `~/.claude/auto-skill.local.md`:

```yaml
---
paths:
  events_db: /custom/path/events.db
  skills_dir: /custom/path/skills
  tracker_db: /custom/path/tracker.db
---
```

---

## Pattern Detection

### How does pattern detection work?

Auto-Skill watches your tool call sequences:

1. **Record**: Logs every tool call (read, edit, bash, etc.)
2. **Analyze**: Detects repeated sequences (min 3 occurrences)
3. **Generate**: Creates SKILL.md with instructions
4. **Track**: Monitors success to adjust confidence

**Example Pattern**:
```
read → edit → bash:pytest → edit
```
Detected as: "TDD Workflow" (85% confidence)

### What counts as a "pattern"?

A pattern needs:

- **Min occurrences**: 3+ times (configurable)
- **Sequence length**: 2-10 tool calls
- **Consistency**: Same order, similar context
- **Success rate**: 70%+ (for high confidence)

### Can I exclude certain patterns?

Yes! Use `.autoignore` in your project root:

```
# Ignore read-only sequences
read,read,read

# Ignore specific tools
*,bash:ls,*

# Ignore files
*/test/*
```

### How do I adjust detection sensitivity?

Edit `~/.claude/auto-skill.local.md`:

```yaml
detection:
  min_occurrences: 5      # Require more occurrences
  min_confidence: 0.8     # Only high-confidence patterns
  lookback_days: 14       # Longer history window
```

---

## Confidence & Graduation

### How does confidence evolution work?

Skills start at different confidence levels based on source:

```
External (skills.sh) → 50% (untested)
    ↓ (3 uses, 70% success)
Proven External → 75% (validated)
    ↓ (5 uses, 80% success)
Local (graduated) → 85% (trusted)
    ↓ (continued success)
Expert (local) → 100% (mastered)
```

Confidence is adjusted after each use based on success.

### What is "graduation"?

Graduation promotes external skills to local after proven success:

**Criteria**:
- Confidence ≥ 85%
- Usage ≥ 5 times
- Success rate ≥ 80%

**Process**:
1. Detect candidate
2. Prompt user (or auto-approve)
3. Generate local SKILL.md
4. Update tracker (promote to local)
5. Reset confidence to 80% (local starting point)

### How do I manually graduate a skill?

```bash
# Interactive (prompts for each)
python -m core.graduation_manager

# Auto-graduate top 5
python -m core.graduation_manager auto 5

# Graduate specific skill
python -m core.graduation_manager graduate skill-name
```

### Can I prevent a skill from graduating?

Yes! Add to skill frontmatter:

```yaml
---
name: my-skill
graduation:
  enabled: false  # Never auto-graduate
---
```

---

## Mental Model Integration

### What is Mental Model?

[Mental](https://github.com/mental-model/mental) is a CLI for externalizing understanding of codebases:

- **Domains**: Nouns (Order, Payment, User)
- **Capabilities**: Verbs (Checkout, ProcessPayment)
- **Aspects**: Cross-cutting (Auth, Validation)
- **Decisions**: The "why" behind architecture

### How does Auto-Skill use Mental?

Mental provides semantic context for skills:

1. **Pattern Enhancement**: "read-edit" → "payment-read-edit" (domain context)
2. **Skill Suggestions**: Suggests skills relevant to current domain
3. **Confidence Boost**: Mental-aligned skills get +10% confidence
4. **Documentation**: Auto-generated docs reference Mental decisions

### Do I need to set up Mental first?

No! Auto-Skill detects Mental automatically:

- **Mental found**: Uses it for enhanced context
- **Mental not found**: Works without it (graceful degradation)

### How do I add Mental to my project?

```bash
# Install Mental CLI
npm install -g @mental-model/cli

# Initialize in your project
cd your-project
mental init

# Add domains
mental add domain "Payment" --desc "Payment processing"
mental add capability "Checkout" --desc "Order checkout flow"

# Auto-Skill will now detect and use these!
```

---

## External Skills (Skills.sh)

### What is skills.sh?

[Skills.sh](https://skills.sh) is a community marketplace with 27,471+ AI agent skills. Auto-Skill integrates it for external discovery.

### How do I search external skills?

```bash
# CLI search
python -m commands.discover --search "payment"

# Web UI search
# Open http://localhost:5000 → Search box
```

### Do external skills work immediately?

Yes, but with lower confidence (50%) until proven:

1. **First use**: 50% confidence (untested)
2. **After 3 uses**: 60-70% (initial validation)
3. **After 5 uses**: 75-85% (proven)
4. **Graduation**: Promoted to local (85%+)

### Can I publish my skills to skills.sh?

Yes! (Note: Publishing API is hypothetical - implementation ready for when skills.sh adds it)

```bash
# Detect publishable skills
python -m core.skillssh_publisher detect

# Publish a skill
python -m core.skillssh_publisher publish skill-name

# Sync community stats
python -m core.skillssh_publisher sync
```

---

## Web UI

### How do I access the Web UI?

```bash
# Start server
cd web
pip install -r requirements.txt
python app.py

# Open browser
# http://localhost:5000
```

### What features does the Web UI have?

**Dashboard**:
- Total skills, local/external breakdown
- Usage stats, success rates
- Top skills by usage

**Skill Browser**:
- Grid view of all skills
- Search/filter functionality
- Confidence bars
- Source badges

**Graduation Tab**:
- Visual candidate cards
- One-click graduation
- Real-time updates

**Publishing Tab**:
- Publishable skills list
- One-click publishing
- Community stats

### Is the Web UI mobile-friendly?

Yes! Responsive design works on:
- Desktop (1920px+)
- Tablet (768px-1920px)
- Mobile (320px-768px)

### Can I customize the Web UI?

Yes! Edit templates:

- **HTML**: `web/templates/index.html`
- **Styling**: Inline CSS (or extract to `web/static/style.css`)
- **Colors**: Search for gradient colors in CSS

---

## CLI Usage

### What CLI commands are available?

**Discovery**:
```bash
python -m commands.discover              # Discover skills
python -m commands.discover --search     # Search external
python -m commands.discover --json       # JSON output
```

**Initialization**:
```bash
python -m commands.init                  # Setup directories
python -m commands.init --force          # Recreate config
```

**Graduation**:
```bash
python -m core.graduation_manager        # Interactive
python -m core.graduation_manager auto 5 # Auto-graduate
```

**Publishing**:
```bash
python -m core.skillssh_publisher detect # Find publishable
python -m core.skillssh_publisher publish <name> # Publish
```

### How do I get JSON output for scripting?

Add `--json` flag:

```bash
# Discover (JSON)
python -m commands.discover --json > skills.json

# Parse with jq
python -m commands.discover --json | jq '.suggestions[] | select(.confidence > 0.8)'
```

### Can I run commands via API?

Yes! The Web UI exposes REST endpoints:

```bash
# Get all skills
curl http://localhost:5000/api/skills

# Graduate a skill
curl -X POST http://localhost:5000/api/graduation/graduate \
  -H "Content-Type: application/json" \
  -d '{"skill_name": "my-skill"}'
```

---

## Troubleshooting

### Skills aren't being detected

**Check**:

1. **Events recorded?** Run: `python -c "from core.event_store import EventStore; print(EventStore('~/.claude/auto-skill/events.db').get_recent_events(10))"`
2. **Min occurrences met?** Default is 3, check config
3. **Sequence too short/long?** Must be 2-10 tools
4. **Recent enough?** Default lookback is 7 days

**Fix**:
```yaml
# Lower thresholds in config
detection:
  min_occurrences: 2  # More sensitive
  lookback_days: 30   # Longer history
```

### Confidence not updating

**Check**:

1. **Tracker database exists?** `~/.claude/auto-skill/skill_tracker.db`
2. **Skill registered?** Run: `python -c "from core.skill_tracker import SkillTracker; print(SkillTracker('~/.claude/auto-skill/skill_tracker.db').get_all_stats())"`

**Fix**:
```bash
# Reset tracker (WARNING: loses history)
rm ~/.claude/auto-skill/skill_tracker.db
python -m commands.init
```

### Mental Model not detected

**Check**:

1. **Mental installed?** Run: `mental --version`
2. **Mental in project?** Check for `mental.json`
3. **Enabled in config?** `enable_mental: true`

**Fix**:
```bash
# Install Mental
npm install -g @mental-model/cli

# Initialize in project
cd your-project
mental init
```

### Web UI won't start

**Check**:

1. **Flask installed?** `pip install flask`
2. **Port 5000 available?** Try: `lsof -i :5000`
3. **Database accessible?** Check paths in `web/app.py`

**Fix**:
```bash
# Install dependencies
cd web
pip install -r requirements.txt

# Use different port
python app.py --port 8080
```

### Graduation not working

**Check**:

1. **Candidates exist?** Run: `python -m core.graduation_manager detect`
2. **Criteria met?** Must be ≥85%, ≥5 uses, ≥80% success

**Debug**:
```bash
# Show detailed stats
python -m core.graduation_manager stats

# Check specific skill
python -c "from core.skill_tracker import SkillTracker; print(SkillTracker('~/.claude/auto-skill/skill_tracker.db').get_skill_stats('skill-name'))"
```

---

## Performance & Limits

### How much data can it handle?

Tested limits:

- **Events**: 10,000+ (< 2s query time)
- **Sessions**: 100+ (< 3s analysis)
- **Skills**: 1,000+ (instant lookup)
- **Database**: 100 MB+ (SQLite scales well)

### Does it slow down over time?

No! Includes:

- **Indices**: On frequently queried columns
- **Cleanup**: Old events can be archived
- **Migrations**: Schema versioning for smooth upgrades

### Can I archive old data?

Yes:

```python
from core.event_store import EventStore
store = EventStore('~/.claude/auto-skill/events.db')

# Archive events older than 30 days
store.archive_old_events(days=30, archive_path='events_archive.db')
```

---

## Contributing & Support

### How can I contribute?

See [Contributing Guide](contributing.md):

1. Fork repository
2. Create feature branch
3. Add tests
4. Submit PR

### Where do I report bugs?

[GitHub Issues](https://github.com/MaTriXy/claude-auto-skill/issues):

- Bug reports
- Feature requests
- Questions

### Is there a community?

Yes!

- **Discord**: [Join server](#) (coming soon)
- **Twitter**: [@MaTriXy](https://twitter.com/MaTriXy)
- **GitHub Discussions**: [Start a discussion](https://github.com/MaTriXy/claude-auto-skill/discussions)

### Can I hire you for custom development?

Yes! Contact via:

- Twitter: [@MaTriXy](https://twitter.com/MaTriXy)
- Email: (via GitHub profile)

---

## Advanced Topics

### Can I use this in CI/CD?

Yes! Headless mode:

```bash
# Generate skills in CI
python run_detector.py --headless --output ci-skills/

# Auto-graduate without prompts
python -m core.graduation_manager auto 10
```

### How do I backup my data?

```bash
# Backup everything
tar -czf auto-skill-backup.tar.gz ~/.claude/auto-skill ~/.claude/skills

# Restore
tar -xzf auto-skill-backup.tar.gz -C ~/
```

### Can I share skills with my team?

Yes! Two approaches:

**1. Git repository**:
```bash
cd ~/.claude/skills
git init
git add auto/
git commit -m "Add team skills"
git remote add origin https://github.com/team/skills.git
git push
```

**2. Publish to skills.sh**:
```bash
python -m core.skillssh_publisher publish skill-name
```

### How do I create a custom skill manually?

Create `~/.claude/skills/auto/my-skill.md`:

```yaml
---
name: my-custom-skill
confidence: 0.80
source: manual
tags: [custom, team]
---

# My Custom Skill

Description here.

## Usage

Instructions here.

## Success Indicators

- Task completed
- No errors
```

---

Still have questions? [Open an issue](https://github.com/MaTriXy/claude-auto-skill/issues) or [start a discussion](https://github.com/MaTriXy/claude-auto-skill/discussions)!
