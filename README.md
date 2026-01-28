# Claude Auto-Skill

**Automatically learn from your workflows and turn them into intelligent, context-aware skills.**

Claude Auto-Skill observes your Claude Code sessions, detects repeated patterns, and generates reusable skills with deep contextual understanding. **Version 2.0 + Hybrid Integration** combines local pattern detection with external skill discovery and Mental Model understanding.

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-green.svg)](https://python.org)
[![Documentation](https://img.shields.io/badge/docs-MkDocs-blue.svg)](https://MaTriXy.github.io/claude-auto-skill)

---

## 🎯 What Makes It Unique

| Feature | Auto-Skill | Alternatives |
|---------|-----------|--------------|
| **Local Pattern Detection** | ✅ Automatic | ❌ Manual |
| **Mental Model Integration** | ✅ First-of-its-kind | ❌ None |
| **External Skill Discovery** | ✅ Skills.sh | ✅ Some |
| **Confidence Evolution** | ✅ 50% → 85% | ❌ None |
| **Auto-Generation** | ✅ Instant | ❌ 15-30 min |
| **Vercel Compatible** | ✅ Full metadata | ⚠️ Limited |
| **V2 Analysis** | ✅ Session + LSP + Patterns | ❌ None |

**ROI**: Save ~25 hours per 100 skills vs manual creation

---

## ✨ What's New in V2 + Hybrid

### V2 Core Features

#### 🧠 Session Analysis
- Detects user intent: debug, implement, refactor, test, explore, document
- Identifies workflow types: TDD, Refactor-Safe, Debug-Systematic, Explore-Then-Implement
- Extracts problem domains from context
- Calculates success indicators

#### 🏗️ LSP Integration
- Python AST analysis for complete code structure
- Extracts classes, functions, methods, decorators
- Builds dependency graphs and import relationships
- Framework for JavaScript/TypeScript support

#### 🎨 Design Pattern Detection
Detects **18 patterns** across three categories:
- **8 Architectural:** MVC, Repository, Factory, Singleton, Strategy, Observer, Adapter, Dependency Injection
- **6 Coding:** Error handling, REST API, Async patterns, Decorators, Context managers, Builders
- **4 Workflow:** TDD, Refactor-Safe, Debug-Systematic, Explore-Then-Implement

### Priority 3 Features (NEW!) 🚀

#### 🎓 Automatic Graduation
- Auto-detect graduation candidates (≥85% confidence, ≥5 uses, ≥80% success)
- Interactive or batch graduation workflows
- External → Local skill promotion
- Complete graduation history tracking

```bash
# Detect and graduate candidates
python -m core.graduation_manager

# Auto-graduate top 5
python -m core.graduation_manager auto 5

# Show stats
python -m core.graduation_manager stats
```

#### 📤 Skills.sh Publishing
- One-command skill publishing
- Community adoption tracking
- Sync install counts and ratings
- Publish/unpublish workflows

```bash
# Detect publishable skills
python -m core.skillssh_publisher detect

# Publish a skill
python -m core.skillssh_publisher publish <skill_name>

# Sync community stats
python -m core.skillssh_publisher sync
```

#### 🌐 Web UI
- Visual skill browser with search/filter
- Real-time adoption dashboard
- Confidence visualization (animated bars)
- One-click graduation & publishing
- Responsive design (desktop + mobile)

```bash
# Easy way: Use the convenience script
./start-web.sh        # macOS/Linux
start-web.bat         # Windows

# Or run manually
cd web
uv sync
python app.py

# Open http://localhost:8000
```

### Hybrid Integration (NEW!)

#### 🧩 Mental Model Integration
**First-of-its-kind codebase semantic understanding:**
- Integrates with [@mentalmodel/cli](https://github.com/Michaelliv/mental)
- Extracts domains (Payment, User, Order)
- Identifies capabilities (Checkout, ProcessPayment)
- Recognizes aspects (Auth, Validation)
- Links to architecture decisions
- Enriches pattern names with domain context

**Example**: Pattern `read-edit-workflow` becomes `payment-read-edit-workflow` when working in payment domain

#### 🌐 External Skill Discovery
**27,471+ community skills from Skills.sh:**
- Search, trending, and detailed skill information
- Tag-based filtering
- Install count tracking
- Cross-agent compatibility

#### 📊 Adoption Tracking & Confidence Evolution
**Skills learn and improve over time:**
- **External skills** start at 50% confidence
- **Proven skills** reach 75% (3+ successful uses)
- **Graduated skills** achieve 85% (5+ uses, 80% success rate)
- Automatic promotion to local skills

#### 🔍 Unified Discovery
**Smart multi-source skill suggestions:**
- Combines local patterns + Mental context + external skills
- Ranks by confidence (local > proven > hints > external)
- Deduplicates and enriches with context
- Context-aware based on current work

---

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (recommended)
pip install claude-auto-skill

# Or clone for development
git clone https://github.com/MaTriXy/claude-auto-skill.git
cd claude-auto-skill
pip install -e ".[dev]"

# Initialize (creates config and directories)
auto-skill init
```

### Optional: Install Mental Model CLI

For semantic understanding of your codebase:

```bash
npm install -g @mentalmodel/cli
cd your-project
mental add domain Payment --desc "Payment processing"
mental add capability Checkout --operates-on Payment
```

### Basic Usage

Once installed, the plugin automatically:
1. ✅ Records your tool usage patterns
2. ✅ Detects repeated workflows (3+ occurrences)
3. ✅ Offers to create skills from high-confidence patterns

---

## 💡 Examples

### Example 1: Discover Skills

```bash
# Discover skills for current project
python -m commands.discover

# Output:
# 🔍 Found 5 skill suggestions:
#
# 1. 🏠 payment-tdd-workflow
#    Test-driven development for payment processing
#    Confidence: [██████████] 85%
#    Source: local
#    Domains: Payment, Order
#
# 2. 🌐 stripe-integration
#    Stripe payment processing
#    Confidence: [████████░░] 75%
#    Source: external
#    Author: community
#    Installs: 150
```

### Example 2: Search External Skills

```bash
# Search Skills.sh for payment skills
python -m commands.discover --search "payment"

# Output:
# 🌐 Searching Skills.sh for: 'payment'
#
# Found 8 skills:
#
# 1. stripe-integration
#    Complete Stripe payment processing
#    Author: community-author
#    Installs: 150
#    Tags: payment, stripe, api
```

### Example 3: Track Adoption

```bash
# Show adoption statistics
python -m commands.discover --stats

# Output:
# 📊 Adoption Statistics
#
# Tracking 3 skills:
#
# 🏠 tdd-workflow ⭐ (graduated)
#    Confidence: [██████████] 85%
#    Usage: 12 times (11 successes)
#
# 🌐 stripe-integration 🔥 (proven)
#    Confidence: [████████░░] 75%
#    Usage: 8 times (7 successes)
```

### Example 4: Find Graduation Candidates

```bash
# Show skills ready to graduate to local
python -m commands.discover --candidates

# Output:
# ⭐ Graduation Candidates
#
# Found 1 skill ready to graduate:
#
# 🌐 payment-retry
#    Confidence: [█████████░] 85%
#    Usage: 6 times (5 successes, 1 failures)
#    Success Rate: 83%
#    Ready to graduate to local skill! ⭐
```

---

## 🏗️ Architecture

### Complete System Overview

```
┌─────────────────────────────────────────────────────┐
│         Claude Auto-Skill V2 + Hybrid                │
├─────────────────────────────────────────────────────┤
│                                                       │
│  📥 INPUT LAYER                                       │
│  ├─ EventStore (SQLite) - Tool usage history        │
│  ├─ Mental Model - Codebase understanding           │
│  └─ Skills.sh API - External discovery              │
│                                                       │
│  🧠 ANALYSIS LAYER                                    │
│  ├─ PatternDetector - Sequence matching             │
│  ├─ SessionAnalyzer - Intent & workflow             │
│  ├─ LSPAnalyzer - Code structure                    │
│  ├─ DesignPatternDetector - Pattern recognition     │
│  └─ MentalAnalyzer - Semantic understanding         │
│                                                       │
│  🔍 DISCOVERY LAYER                                   │
│  ├─ UnifiedSuggester - Multi-source ranking         │
│  ├─ SkillsShClient - External skill search          │
│  └─ SkillTracker - Adoption tracking                │
│                                                       │
│  ⚙️  GENERATION LAYER                                 │
│  ├─ SkillGenerator - SKILL.md creation              │
│  └─ Metadata enrichment (Vercel-compatible)         │
│                                                       │
│  📤 OUTPUT LAYER                                      │
│  ├─ SKILL.md files (rich metadata)                  │
│  ├─ CLI tools (discover, stats)                     │
│  └─ JSON export (for automation)                    │
└─────────────────────────────────────────────────────┘
```

### Confidence Evolution

```
External Skill (50%)
      ↓ (3+ uses, 70% success)
Proven Skill (75%)
      ↓ (5+ uses, 80% success)
Local Skill (85%)
```

---

## 📖 Usage Patterns

### Pattern Detection

Patterns are detected when:
- Same tool sequence appears **3+ times** across sessions
- Sequence is **2-10 tools** long
- Pattern occurred within the last **7 days**

### Confidence Scoring

| Factor | Weight | Description |
|--------|--------|-------------|
| Occurrences | 40% | More repetitions = higher confidence |
| Length | 20% | 3-5 tools is ideal |
| Success Rate | 25% | Patterns that succeed score higher |
| Recency | 15% | Recent patterns prioritized |

**Hybrid Enhancement:** Mental context and adoption tracking boost confidence

### Generated Skill Example

```yaml
---
name: payment-read-edit-workflow
description: Process payment transactions with TDD approach
confidence: 0.85
occurrence-count: 7

# V2 metadata
session-analysis:
  primary_intent: implement
  workflow_type: TDD
  tool_success_rate: 0.95

# Hybrid: Mental context
mental-context:
  domains: [Payment, Order]
  capabilities: [Checkout, ProcessPayment]
  aspects: [Validation, Auth]

# Hybrid: Vercel compatibility
compatible-agents: [claude-code, opencode, codex]
tags: [read, edit, implement, tdd, payment]
source: auto-generated
derived-from: local-patterns
---

# payment-read-edit-workflow

Process payment transactions using test-driven development.

## Steps

1. Read the payment processing code
2. Write tests for new payment scenarios
3. Implement payment logic
4. Run tests to verify
...
```

---

## 🛠️ Commands

### Unified CLI

All commands use the `auto-skill` entry point:

```bash
# Core commands
auto-skill init                # Initialize auto-skill config and directories
auto-skill discover            # Discover skills for current project
auto-skill search "query"      # Search external skills
auto-skill stats               # Show adoption statistics
auto-skill graduate            # Manage skill graduation

# Agent management
auto-skill agents list         # List known agents
auto-skill agents detect       # Detect installed agents

# Lock file (integrity verification)
auto-skill lock status         # Show lock file status
auto-skill lock verify         # Verify skill integrity (SHA-256)
auto-skill lock list           # List locked skills

# Telemetry
auto-skill telemetry report    # Show effectiveness report
auto-skill telemetry events    # Show raw events

# Utility
auto-skill version             # Show version

# All commands support JSON output
auto-skill discover --json
auto-skill agents list --json
auto-skill lock status --json
```

### Configuration

Create `~/.claude/auto-skill.local.md` to customize:

```yaml
---
detection:
  min_occurrences: 3         # Minimum pattern repetitions
  min_sequence_length: 2     # Shortest pattern to detect
  max_sequence_length: 10    # Longest pattern to detect
  lookback_days: 7           # Analysis window
  min_confidence: 0.7        # Threshold for suggestions

# Hybrid configuration
hybrid:
  enable_mental: true        # Enable Mental model integration
  enable_external: true      # Enable Skills.sh discovery
  auto_graduate: true        # Auto-graduate proven skills

enabled: true
---
```

---

## 🧪 Development

### Run Tests

```bash
# All tests
pytest tests/ -v

# Specific test suites
pytest tests/test_v2_integration.py -v
pytest tests/test_phase3_integration.py -v

# With coverage
pytest tests/ --cov=core --cov-report=html
```

### Project Structure

```
claude-auto-skill/
├── core/                           # Core modules
│   ├── path_security.py           # Path traversal protection
│   ├── spec_validator.py          # agentskills.io spec compliance
│   ├── agent_registry.py         # Multi-agent detection & symlinks
│   ├── lock_file.py               # SHA-256 integrity lock file
│   ├── telemetry.py               # Anonymous telemetry (local + remote)
│   ├── providers/                 # Pluggable skill providers
│   │   ├── base.py               # SkillProvider protocol
│   │   ├── manager.py            # Multi-provider orchestration
│   │   ├── local_provider.py     # Local ~/.claude/skills/ search
│   │   ├── skillssh_provider.py  # Skills.sh integration
│   │   └── wellknown_provider.py # RFC 8615 discovery
│   ├── pattern_detector.py       # Pattern detection + Mental
│   ├── skill_generator.py        # Skill generation + Vercel
│   ├── mental_analyzer.py        # Mental Model integration
│   ├── skillssh_client.py        # Skills.sh API
│   ├── skill_tracker.py          # Adoption tracking
│   ├── unified_suggester.py      # Multi-source discovery
│   ├── session_analyzer.py       # V2 session analysis
│   ├── lsp_analyzer.py           # V2 code structure
│   └── design_pattern_detector.py # V2 patterns
├── commands/
│   ├── cli.py                     # Unified CLI entry point
│   ├── discover.py                # Discovery subcommand
│   ├── init.py                    # Initialization subcommand
│   ├── agents.py                  # Agent management subcommand
│   ├── lock.py                    # Lock file subcommand
│   └── telemetry_cmd.py          # Telemetry subcommand
├── hooks/                         # Event capture hooks
├── tests/                         # Test suites
├── skills/                        # Generated skills
└── .github/workflows/publish.yml  # PyPI publish on tagged releases
```

---

## 🌟 External Skills

### Featured Skills

#### Karpathy Guidelines
**Source**: [forrestchang/andrej-karpthy-skills](https://github.com/forrestchang/andrej-karpthy-skills)

Behavioral guidelines to reduce LLM coding mistakes, based on Andrej Karpathy's observations:

1. **Think Before Coding** - No assumptions, surface tradeoffs
2. **Simplicity First** - Minimum code that works
3. **Surgical Changes** - Touch only what you must
4. **Goal-Driven Execution** - Define success criteria

**Install**:
```bash
# Already included in skills/external/karpathy-guidelines/
```

---

## 📊 Comparison with Alternatives

| Feature | Auto-Skill | Vercel Skills | Manual |
|---------|-----------|---------------|--------|
| Pattern Detection | ✅ Automatic | ❌ Manual | ❌ Manual |
| Skill Generation | ✅ Instant | ❌ Manual | ❌ 15-30 min |
| Mental Model | ✅ Yes | ❌ No | ❌ No |
| External Discovery | ✅ Yes | ✅ Yes | ❌ No |
| Adoption Tracking | ✅ Yes | ❌ No | ❌ No |
| Auto-Graduation | ✅ Yes | ❌ No | ❌ No |
| V2 Analysis | ✅ Yes | ❌ No | ❌ No |

**Conclusion**: Auto-Skill is the most comprehensive system available

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

### High Priority
- [ ] Complete JavaScript/TypeScript LSP support
- [ ] Add skill publishing to Skills.sh
- [ ] Web UI for skill management
- [ ] PyPI package for easy installation

### Medium Priority
- [ ] More design patterns (currently 18)
- [ ] Database migration system
- [ ] Performance optimization for large datasets
- [ ] Integration tests for all workflows

### Low Priority
- [ ] Cross-project pattern sharing
- [ ] Pattern merging and evolution
- [ ] Visual pattern explorer

---

## 📚 Documentation

- **Installation & Setup**: [Getting Started](#-quick-start)
- **User Guide**: [Usage Patterns](#-usage-patterns)
- **Architecture**: [System Overview](#-architecture)
- **API Reference**: See docstrings in `core/` modules
- **Phase Documentation**: See `planning/` directory
  - `HYBRID_INTEGRATION_PLAN.md` - Complete implementation plan
  - `PHASE2_COMPLETE.md` - Unified discovery layer
  - `PHASE3_COMPLETE.md` - Pattern integration
- **Project Review**: `PROJECT_REVIEW.md` (comprehensive analysis)

---

## 📚 Documentation

**Comprehensive documentation is available at: [https://MaTriXy.github.io/claude-auto-skill](https://MaTriXy.github.io/claude-auto-skill)**

### Documentation Includes:

- **Getting Started**: Installation, quick start, configuration
- **Features**: Complete feature documentation with examples
- **User Guide**: CLI commands, workflows, best practices
- **API Reference**: Architecture and API documentation
- **FAQ**: 40+ common questions answered

### Build Documentation Locally

```bash
pip install -r requirements-docs.txt
mkdocs serve
# Open http://localhost:8000
```

---

## 🔐 V3.0 Features

### Path Security

All skill names and file paths are validated to prevent path traversal attacks:
- Names sanitized to spec-compliant kebab-case (max 64 chars)
- Unicode NFKD normalization
- Null byte and `../` injection blocked
- Symlink escape prevention

### agentskills.io Spec Compliance

Generated skills are validated against the [agentskills.io](https://agentskills.io) spec:
- Name format: `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$`
- Description max 1024 chars
- `allowed-tools` as YAML list (not comma string)
- `version` field required

### Agent Registry

Detects and manages 10 coding agents:

| Agent | Detection | Skill Directory |
|-------|-----------|-----------------|
| Claude Code | `CLAUDE_CODE` env | `~/.claude/skills/` |
| OpenCode | `OPENCODE` env | `~/.opencode/skills/` |
| Codex | `CODEX_CLI` env | `~/.codex/skills/` |
| Continue | `CONTINUE` env | `~/.continue/skills/` |
| Aider | `AIDER` env | `~/.aider/skills/` |
| Cursor | `CURSOR` env | `~/.cursor/skills/` |
| Windsurf | `WINDSURF` env | `~/.windsurf/skills/` |
| Cline | `CLINE` env | `~/.cline/skills/` |
| Amp | `AMP` env | `~/.amp/skills/` |
| Copilot | `GITHUB_COPILOT` env | `~/.copilot/skills/` |

Skills are automatically symlinked to all detected agents for cross-agent sharing.

### Provider System

Pluggable skill discovery via the `SkillProvider` protocol:

- **LocalProvider** — searches `~/.claude/skills/`
- **SkillsShProvider** — queries skills.sh
- **WellKnownProvider** — RFC 8615 `/.well-known/agent-skills.json` discovery

Add custom providers by implementing the `SkillProvider` protocol.

### Lock File

Integrity verification using SHA-256 content hashes:

```bash
auto-skill lock status    # Show lock file info
auto-skill lock verify    # Verify all skill hashes
auto-skill lock list      # List locked skills with hashes
```

Lock file stored at `~/.claude/auto-skill/skills.lock.json` with atomic writes.

---

## Telemetry Disclosure

> **Notice:** This tool collects anonymous usage data to help improve the experience.
> This is **enabled by default** but can be easily disabled.

### What We Collect

We collect **anonymous, aggregate metrics only**:

| Data | Example | Purpose |
|------|---------|---------|
| Event type | `skill_used`, `search` | Know which features are used |
| Result counts | `5 results` | Understand effectiveness |
| Timing | `45ms` | Monitor performance |
| Outcome | `success` / `failure` | Track skill reliability |
| Agent name | `claude-code` | Ensure compatibility |
| System info | `darwin`, `python 3.12` | Ensure compatibility |
| Tool version | `3.0.0` | Track adoption |

### What We Do NOT Collect

- **No search queries** - We never see what you search for
- **No file names or paths** - We don't know which files you access
- **No session IDs** - We don't track individual sessions
- **No skill content** - We don't see your skill definitions
- **No IP addresses** - We don't track your location
- **No personal information** - Completely anonymous

### Disable Telemetry

```bash
# Option 1: Tool-specific
export AUTO_SKILL_NO_TELEMETRY=1

# Option 2: Universal standard (works with other tools too)
export DO_NOT_TRACK=1
```

Add to your `~/.bashrc` or `~/.zshrc` to disable permanently.

### Automatic Opt-Out

Telemetry is **automatically disabled** in CI environments:
- GitHub Actions, GitLab CI, CircleCI, Travis CI, Buildkite, Jenkins

### Transparency

The telemetry implementation is fully open source: [`core/telemetry.py`](core/telemetry.py)

---

## 🔧 Troubleshooting

### Mental Model not found

```bash
# Install Mental CLI
npm install -g @mentalmodel/cli

# Verify installation
mental --version
```

### Skills.sh API timeout

Check your internet connection. Skills.sh client has 10-second timeout and graceful fallback.

### Pattern detection not working

Check event store:
```bash
# Verify events are being recorded
sqlite3 ~/.claude/auto-skill/events.db "SELECT COUNT(*) FROM tool_events"
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## 🙏 Credits

- **V2 Architecture**: Inspired by LSP and modern code intelligence tools
- **Mental Model**: Integration with [@mentalmodel/cli](https://github.com/Michaelliv/mental)
- **Skills.sh**: External discovery via [Vercel Labs Skills](https://skills.sh)
- **Karpathy Guidelines**: [forrestchang/andrej-karpthy-skills](https://github.com/forrestchang/andrej-karpthy-skills)
- Built for [Claude Code](https://claude.ai/code)

---

## 🔗 Links

- **Repository**: https://github.com/MaTriXy/claude-auto-skill
- **Issues**: https://github.com/MaTriXy/claude-auto-skill/issues
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Skills.sh**: https://skills.sh

---

**Version**: 3.0.0
**Status**: Production Ready

---

*Built with ❤️ by [MaTriXy](https://github.com/MaTriXy)*
