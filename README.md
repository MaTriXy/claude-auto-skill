# Claude Auto-Skill

**Automatically learn from your workflows and turn them into intelligent, context-aware skills.**

Claude Auto-Skill observes your Claude Code sessions, detects repeated patterns, and generates reusable skills with deep contextual understanding. **Version 2.0** adds session analysis, code structure awareness, and design pattern recognition.

## What's New in V2 🎉

V2 transforms Claude Auto-Skill from a pattern detector into an **intelligent learning system**:

| V1 | V2 |
|----|----|
| Detects tool sequences | **+ Understands user intent & context** |
| Basic skill generation | **+ Rich skills with design patterns & code awareness** |
| Tool pattern matching | **+ Session analysis & problem-solving approaches** |
| No code understanding | **+ Full LSP integration (classes, functions, dependencies)** |

### V2 Core Features

#### 🧠 Session Analysis
- Analyzes full conversation context (not just tools)
- Detects user intent: debug, implement, refactor, test, explore, document
- Identifies workflow types: TDD, Refactor-Safe, Debug-Systematic, Explore-Then-Implement
- Extracts problem domains from context

#### 🏗️ LSP Integration
- Python AST analysis for complete code structure
- Extracts classes, functions, methods, decorators
- Builds dependency graphs and import relationships
- Symbol extraction with metadata
- Framework for JavaScript/TypeScript support

#### 🎨 Design Pattern Detection
Detects **18 patterns** across three categories:
- **8 Architectural:** MVC, Repository, Factory, Singleton, Strategy, Observer, Adapter, Dependency Injection
- **6 Coding:** Error handling, REST API, Async patterns, Decorators, Context managers, Builders
- **4 Workflow:** TDD, Refactor-Safe, Debug-Systematic, Explore-Then-Implement

#### 📝 Enhanced Skill Generation
Generated skills now include:
- Contextual understanding (why patterns work)
- Code structure awareness (when to apply)
- Design pattern metadata
- Problem-solving approach guidance

## How It Works

### Pattern Detection Flow

```
Session 1: Grep → Read → Edit    ─┐
Session 2: Grep → Read → Edit     ├──▶  V2 Analysis Pipeline
Session 3: Grep → Read → Edit    ─┘          │
                                             ▼
                      ┌──────────────────────────────────────┐
                      │  Session Analysis                    │
                      │  • Intent: refactor                  │
                      │  • Workflow: Refactor-Safe           │
                      │  • Domain: authentication            │
                      └──────────────────────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────┐
                      │  LSP Analysis                        │
                      │  • Classes: [UserAuth, AuthService]  │
                      │  • Functions: [login, validate]      │
                      │  • Dependencies: db.repository       │
                      └──────────────────────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────┐
                      │  Pattern Detection                   │
                      │  • Architectural: Repository         │
                      │  • Workflow: Refactor-Safe           │
                      │  • Confidence: 0.85                  │
                      └──────────────────────────────────────┘
                                             │
                                             ▼
                              "refactor-safe-workflow"
                           with rich V2 metadata
                                             │
                                             ▼
                                ~/.claude/skills/auto/
```

## Installation

### Prerequisites

- Python 3.9+
- Claude Code installed
- Git

### Install V2

```bash
# Clone to plugins directory
git clone https://github.com/MaTriXy/claude-auto-skill ~/.claude/plugins/auto-skill

# Install dependencies (V2 includes LSP support)
cd ~/.claude/plugins/auto-skill
pip install -r requirements.txt
```

### Dependencies

V2 requires additional dependencies for advanced features:

```
PyYAML>=6.0              # Core dependency
pygls>=1.3.0             # LSP support
tree-sitter>=0.21.0      # Code parsing
tree-sitter-python       # Python language support
numpy>=1.24.0            # Pattern recognition
scikit-learn>=1.3.0      # ML-based analysis
```

## Usage

### Basic Usage (V1 Compatible)

Once installed, the plugin automatically:
1. Records your tool usage patterns
2. Detects repeated workflows
3. Offers to create skills from high-confidence patterns

### V2 Enhanced Usage

Enable V2 features in your workflow:

```python
from core import PatternDetector, EventStore

# Initialize with V2 enabled
store = EventStore()
detector = PatternDetector(store, enable_v2=True, project_path="/your/project")

# Detect patterns with full V2 analysis
patterns = detector.detect_patterns(min_occurrences=3)

for pattern in patterns:
    print(f"Pattern: {pattern.suggested_name}")
    print(f"Confidence: {pattern.confidence}")
    
    # V2 enhancements
    if pattern.session_context:
        print(f"Intent: {pattern.session_context['primary_intent']}")
        print(f"Workflow: {pattern.session_context['workflow_type']}")
    
    if pattern.design_patterns:
        print(f"Design Patterns: {[p['name'] for p in pattern.design_patterns]}")
    
    if pattern.code_context:
        print(f"Code Structure: {pattern.code_context['detected_symbols']}")
```

## Commands

```bash
/auto-skill:status              # Show system stats
/auto-skill:review              # List detected patterns
/auto-skill:review approve ID   # Create skill from pattern
/auto-skill:load <name>         # Load a skill mid-session
```

## V2 Enhanced Skills Example

V1 skills were basic step lists. V2 skills include rich metadata:

```yaml
---
name: refactor-safe-workflow
description: Safe refactoring with continuous testing

# V1 fields (preserved)
context: fork
allowed-tools: Read, Edit, Bash
confidence: 0.92

# V2: Session Analysis
session-analysis:
  primary-intent: refactor
  workflow-type: Refactor-Safe
  problem-domains: [authentication, api]
  tool-success-rate: 0.95

# V2: Design Patterns
design-patterns:
  - name: Repository
    type: architectural
    confidence: 0.75
    description: Repository pattern for data access abstraction
  - name: Refactor-Safe
    type: workflow
    confidence: 0.85
    description: Safe refactoring with continuous testing

# V2: Code Context
code-context:
  analyzed-files: 5
  detected-symbols:
    classes: [UserAuth, AuthService]
    functions: [login, validate, authenticate]
  dependencies:
    - source: auth/user.py
      target: db.repository

# V2: Problem-Solving Approach
problem-solving-approach:
  type: Refactor-Safe
  when-to-use: When improving code structure without changing behavior
  benefits:
    - Maintains test coverage throughout
    - Reduces risk of introducing bugs
    - Clear rollback points
  steps:
    - Read and understand current implementation
    - Identify refactoring opportunities
    - Make small, incremental changes
    - Run tests after each change
---

# Refactor-Safe Workflow

## Context

Use this workflow when you need to improve code structure without changing behavior.
Common in: Legacy code cleanup, performance optimization, code consolidation.

## Design Patterns Involved

### Repository Pattern
Abstracts data access layer for better testability and maintainability.

### Refactor-Safe Approach
Ensures changes are safe through continuous testing and incremental modifications.

## Steps

1. **Read & Understand**
   - Review current implementation
   - Identify code smells
   - Check existing test coverage

2. **Plan Refactoring**
   - Identify specific improvements
   - Prioritize changes by risk/benefit
   - Ensure tests exist for behavior

3. **Incremental Changes**
   - Make one small change at a time
   - Run tests after each modification
   - Commit working state before next change

4. **Verify & Document**
   - Ensure all tests pass
   - Document architectural changes
   - Update related documentation

## When to Use

✅ Improving code structure
✅ Consolidating duplicated code
✅ Modernizing legacy patterns
✅ Performance optimization
✅ Strong test coverage exists

❌ Adding new features (use TDD instead)
❌ Fixing bugs (use Debug-Systematic)
❌ No test coverage (add tests first)

## Code Structure

This workflow is ideal when working with:
- Repository pattern implementations
- Service layers with dependency injection
- Well-tested business logic
- Modular architectures

## Related Skills

- `tdd-workflow` - For adding new features
- `debug-systematic` - For fixing bugs
- `repository-pattern-implementation` - For data layer refactoring
```

## Pattern Detection

### What Gets Detected

Patterns are detected when:
- Same tool sequence appears **3+ times** across sessions
- Sequence is **2-10 tools** long
- Pattern occurred within the last **7 days**

### V2 Enhanced Detection

V2 adds contextual analysis:
- User intent from conversation
- Problem domains from file paths
- Code structure from LSP analysis
- Design patterns from code and workflows

### Confidence Scoring

| Factor | Weight | Description |
|--------|--------|-------------|
| Occurrences | 40% | More repetitions = higher confidence |
| Length | 20% | 3-5 tools is ideal |
| Success Rate | 25% | Patterns that succeed score higher |
| Recency | 15% | Recent patterns prioritized |

**V2 adds:** Session context quality, code structure richness, pattern match strength

## Configuration

Create `~/.claude/auto-skill.local.md` to customize:

```yaml
---
detection:
  min_occurrences: 3         # Minimum pattern repetitions
  min_sequence_length: 2     # Shortest pattern to detect
  max_sequence_length: 10    # Longest pattern to detect
  lookback_days: 7           # Analysis window
  min_confidence: 0.7        # Threshold for suggestions
  ignored_tools:             # Tools to exclude
    - AskUserQuestion

# V2 Configuration
v2:
  enable_session_analysis: true
  enable_lsp_analysis: true
  enable_pattern_detection: true
  lsp_languages:
    - python
    - javascript
    - typescript
  
enabled: true
---
```

## File Structure

```
claude-auto-skill/
├── core/
│   ├── event_store.py               # Event storage (SQLite)
│   ├── sequence_matcher.py          # Pattern matching algorithm
│   ├── config.py                    # Configuration
│   ├── session_analyzer.py          # V2: Session analysis
│   ├── lsp_analyzer.py              # V2: Code structure
│   ├── design_pattern_detector.py   # V2: Pattern recognition
│   ├── pattern_detector.py          # Enhanced with V2
│   └── skill_generator.py           # Enhanced with V2
├── tests/
│   └── test_v2_integration.py       # V2 integration tests
├── scripts/
│   ├── skill_registry.py            # Skill index
│   ├── list_skills.py               # List all skills
│   └── discover_skill.py            # Discovery + loading
├── README.md
├── CHANGELOG.md                      # Version history
└── requirements.txt                  # Dependencies
```

## Data Storage

| Data | Location | Description |
|------|----------|-------------|
| Events | `~/.claude/auto-skill/events.db` | SQLite database of tool calls |
| Skills | `~/.claude/skills/auto/` | Generated SKILL.md files |
| Registry | `references/registry.json` | Skill index |

### Privacy

- All data is stored **locally** on your machine
- No data sent to external services
- Old events cleaned up after 30 days

## Development

### Run Tests

```bash
cd ~/.claude/plugins/auto-skill
pytest tests/ -v
```

### V2 Integration Tests

```bash
# Run V2-specific tests
pytest tests/test_v2_integration.py -v

# Test specific features
pytest tests/test_v2_integration.py::TestSessionAnalyzer -v
pytest tests/test_v2_integration.py::TestLSPAnalyzer -v
pytest tests/test_v2_integration.py::TestDesignPatternDetector -v
```

## Backward Compatibility

✅ **V2 is 100% backward compatible with V1**

- All V1 features work unchanged
- V1 API completely preserved
- V2 features are opt-in via feature flags
- Graceful degradation if dependencies missing

To use V1 only (no V2 features):

```python
detector = PatternDetector(store, enable_v2=False)
```

## Contributing

Contributions welcome! Areas for improvement:

### V2 Enhancements
- [ ] Complete tree-sitter implementation for JS/TS
- [ ] Add more design patterns (currently 18)
- [ ] Enhanced pattern context documentation
- [ ] NLP-based intent detection
- [ ] Visual pattern explorer

### V1 Improvements
- [ ] Pattern merging and evolution
- [ ] Better duplicate detection
- [ ] Cross-project pattern sharing

## License

MIT - See LICENSE file

## Credits

- Inspired by [Agent Registry](https://github.com/MaTriXy/Agent-Registry) lazy-loading pattern
- Built for [Claude Code](https://claude.ai/code)
- V2 architecture inspired by LSP and modern code intelligence tools

---

**Version:** 2.0.0  
**Repository:** https://github.com/MaTriXy/claude-auto-skill  
**Documentation:** See CHANGELOG.md for detailed V2 release notes
