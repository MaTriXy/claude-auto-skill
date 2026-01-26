# Claude Auto-Skill v2

**Automatically learn from your workflows and turn them into reusable skills with contextual understanding.**

## 🎯 What's New in V2

V2 goes beyond simple tool pattern detection to understand:

- **Full Session Context** - Not just tool sequences, but conversation context, decisions, and problem-solving approaches
- **Code Structure Awareness** - LSP integration understands your codebase architecture
- **Design Pattern Recognition** - Detects architectural, coding, and workflow patterns
- **Contextual Skills** - Generated skills explain when, why, and how to use them

### V1 vs V2 Comparison

| Feature | V1 | V2 |
|---------|----|----|
| Tool Pattern Detection | ✅ | ✅ |
| Confidence Scoring | ✅ | ✅ Enhanced |
| Session History | ❌ | ✅ Full conversation context |
| Code Analysis | ❌ | ✅ LSP integration |
| Design Patterns | ❌ | ✅ Architectural + Coding + Workflow |
| Contextual Understanding | ❌ | ✅ When/Why/How guidance |
| Problem-Solving Approaches | ❌ | ✅ TDD, Refactor, Debug strategies |

## 🚀 Quick Start

### Installation

```bash
cd /Users/iqtmedia/clawd/claude-auto-skill
pip install -r requirements.txt
```

### Basic Usage

The plugin works automatically once installed. It observes your Claude Code sessions and:

1. **Records** tool usage patterns with full context
2. **Analyzes** sessions for intent, workflow, and problem-solving approaches
3. **Detects** design patterns in your code
4. **Generates** rich skills with contextual understanding

### V2-Enhanced Workflow

```
You use Claude Code normally...
   │
   ├─▶ V1: Records tool sequences
   ├─▶ V2: Analyzes session context (intent, workflow type)
   ├─▶ V2: Scans code structure (LSP)
   └─▶ V2: Detects design patterns
   
Pattern detected after 3+ occurrences...
   │
   ├─▶ V1: Calculates confidence from frequency
   ├─▶ V2: Enriches with session insights
   ├─▶ V2: Adds code structure metadata
   └─▶ V2: Includes design pattern info
   
Skill generated...
   │
   └─▶ Rich SKILL.md with:
       - Tool pattern (V1)
       - Session context (V2)
       - Code awareness (V2)
       - Design patterns (V2)
       - Problem-solving approach (V2)
```

## 📋 Requirements

### Core Dependencies
- Python 3.10+
- PyYAML >= 6.0

### V2 Dependencies
- **LSP Support:** `pygls>=1.3.0`, `tree-sitter>=0.21.0`
- **Code Analysis:** `tree-sitter-python`, `tree-sitter-javascript`, `tree-sitter-typescript`
- **Pattern Recognition:** `numpy>=1.24.0`, `scikit-learn>=1.3.0`

## 🏗️ Architecture

### Core Modules

```
core/
├── event_store.py           # SQLite event storage (V1)
├── sequence_matcher.py      # Subsequence detection (V1)
├── pattern_detector.py      # Enhanced with V2 analyzers
├── skill_generator.py       # Generates V2-format skills
├── session_analyzer.py      # NEW: Full session analysis
├── lsp_analyzer.py          # NEW: Code structure analysis
├── design_pattern_detector.py  # NEW: Pattern recognition
└── config.py                # Configuration management
```

### V2 Analysis Pipeline

```
┌─────────────────────────────────────────────────────┐
│              SESSION OBSERVATION                     │
│  Records: Tools + Inputs + Outputs + Context        │
└───────────────────┬─────────────────────────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
┌────────▼──────────┐  ┌───────▼────────────┐
│ Session Analyzer  │  │   LSP Analyzer     │
│                   │  │                    │
│ • Conversation    │  │ • Code symbols     │
│ • Intent          │  │ • Dependencies     │
│ • Workflow type   │  │ • Type info        │
│ • Decisions       │  │ • Structure        │
└────────┬──────────┘  └───────┬────────────┘
         │                     │
         └──────────┬──────────┘
                    │
         ┌──────────▼───────────────┐
         │  Design Pattern Detector  │
         │                           │
         │  • Architectural patterns │
         │  • Coding patterns        │
         │  • Workflow patterns      │
         └──────────┬────────────────┘
                    │
         ┌──────────▼───────────────┐
         │   Enhanced Skills        │
         │                          │
         │   V1: Tool patterns      │
         │   V2: + Context          │
         │       + Code structure   │
         │       + Design patterns  │
         │       + Approach         │
         └──────────────────────────┘
```

## 🎨 Enhanced SKILL Format

V2 skills include rich metadata:

```yaml
---
name: refactor-auth-workflow-a1b2c3
description: Safe refactoring workflow for authentication code

# V1 fields
context: fork
agent: general-purpose
allowed-tools: Read, Edit, Bash
auto-generated: true
confidence: 0.85
occurrence-count: 5

# V2: Session Analysis
session-analysis:
  primary-intent: refactor
  problem-domains: [authentication, api]
  workflow-type: Refactor-Safe
  tool-success-rate: 0.92

# V2: Design Patterns
design-patterns:
  - name: Repository
    type: architectural
    confidence: 0.75
  - name: Error-First-Handling
    type: coding
    confidence: 0.68

# V2: Code Context
code-context:
  analyzed-files: 5
  primary-languages: [python]

# V2: Problem-Solving Approach
problem-solving-approach:
  type: Refactor-Safe
  description: Safe refactoring with continuous testing
---

# refactor-auth-workflow-a1b2c3

Safe refactoring workflow for authentication-related code.

## Context

This workflow is most appropriate when:
- You are improving code structure
- Working in these areas: authentication, api
- Following a Refactor-Safe approach

Success rate: 92%

## Detected Patterns

### Repository (architectural, confidence: 75%)
- **Description:** Repository pattern for data access abstraction
- **When to use:** Abstracting data access layer
- **Benefits:** Decouples business logic, Testable

### Error-First-Handling (coding, confidence: 68%)
- **Description:** Error-first error handling pattern

## Steps

1. Read and understand the current implementation (Read)
2. Identify code smells and refactoring opportunities
3. Make small, incremental changes (Edit)
4. Run tests after each change (Bash)
5. Commit working state before next refactor

## Code Structure Awareness

**Key Classes:**
- `AuthRepository` (src/auth/repository.py:15)
- `AuthService` (src/auth/service.py:25)

**Key Functions:**
- `validate_user` (src/auth/validators.py:10)
- `authenticate` (src/auth/service.py:45)
```

## 🔧 Configuration

Create `~/.claude/auto-skill.local.md` to customize:

```yaml
---
detection:
  min_occurrences: 3
  min_confidence: 0.7
  lookback_days: 7

v2:
  session_analysis:
    enabled: true
    store_conversations: false  # Privacy: don't store full text
    
  lsp_analysis:
    enabled: true
    languages: [python, javascript, typescript]
    use_tree_sitter: true
    
  design_patterns:
    enabled: true
    min_confidence: 0.5
    pattern_types: [architectural, coding, workflow]
---
```

## 🧪 Example: TDD Workflow Detection

When you repeatedly use this pattern:

```
Write test → Run tests (fail) → Edit code → Run tests (pass) → Refactor
```

V2 detects:

**Tool Pattern (V1):**
- Sequence: `Write → Bash → Edit → Bash → Edit`
- Confidence: 0.85 (occurred 5 times)

**Session Context (V2):**
- Intent: `test` (detected from conversation)
- Workflow: `TDD` (recognized Test-Driven Development)
- Success rate: 95%

**Design Pattern (V2):**
- Workflow pattern: `TDD` (confidence: 0.9)
- Context: "Write failing test, make it pass, refactor"

**Generated Skill:**
```yaml
---
name: tdd-workflow-a1b2c3
problem-solving-approach:
  type: TDD
  when-to-use: Building new features or fixing bugs
  steps:
    - Write a failing test
    - Run tests (Red)
    - Write minimal code to pass
    - Run tests (Green)
    - Refactor
  benefits:
    - Better test coverage
    - Forces thinking about requirements
    - Refactoring confidence
---

# tdd-workflow-a1b2c3

Test-Driven Development workflow detected from your usage.

## Context

Use this when:
- Building new features
- Fixing bugs with test coverage
- You want high confidence in changes

## Steps

1. Write a failing test that defines desired behavior (Write)
2. Run tests to confirm the failure - Red (Bash)
3. Write minimal code to make the test pass (Edit)
4. Run tests to confirm they pass - Green (Bash)
5. Refactor code while keeping tests green (Edit)

## Benefits

- Forces you to think about requirements first
- Built-in regression prevention
- Confidence when refactoring later
```

## 🎓 Detected Pattern Types

### Architectural Patterns (from Code)
- **MVC** - Model-View-Controller separation
- **Repository** - Data access abstraction
- **Factory** - Object creation
- **Singleton** - Single instance
- **Strategy** - Interchangeable algorithms
- **Observer** - Event handling
- **Adapter** - Interface compatibility
- **Dependency Injection** - DI containers

### Coding Patterns (from Code)
- **Error-First-Handling** - Try/except patterns
- **REST-API-Design** - RESTful endpoints
- **Async-Pattern** - Async/await usage
- **Decorator-Pattern** - Python decorators
- **Context-Manager** - With statements
- **Builder-Pattern** - Fluent builders

### Workflow Patterns (from Sessions)
- **TDD** - Test-Driven Development
- **Refactor-Safe** - Safe refactoring with tests
- **Debug-Systematic** - Systematic debugging
- **Explore-Then-Implement** - Understanding before building

## 📊 API Usage

### Python API

```python
from core import EventStore, PatternDetector, SkillGenerator, SessionAnalyzer, LSPAnalyzer

# Initialize (V2-enabled by default)
store = EventStore()
detector = PatternDetector(store, enable_v2=True)

# Detect patterns with V2 analysis
patterns = detector.detect_patterns(
    project_path="/path/to/project",
    min_occurrences=3,
    min_confidence=0.7
)

# Patterns include V2 metadata
for pattern in patterns:
    print(f"Pattern: {pattern.suggested_name}")
    print(f"Confidence: {pattern.confidence}")
    
    # V2 additions
    if pattern.session_context:
        print(f"Intent: {pattern.session_context['primary_intent']}")
        print(f"Workflow: {pattern.session_context['workflow_type']}")
    
    if pattern.design_patterns:
        for dp in pattern.design_patterns:
            print(f"Design Pattern: {dp['name']} ({dp['confidence']})")

# Generate V2-enhanced skill
generator = SkillGenerator()
candidate = generator.generate_candidate(pattern)
skill_path = generator.save_skill(candidate)
print(f"Skill saved: {skill_path}")
```

### LSP Analysis

```python
from core import LSPAnalyzer
from pathlib import Path

analyzer = LSPAnalyzer()
structure = analyzer.analyze_project(Path("/path/to/project"))

# Query code structure
classes = analyzer.find_symbols_by_type(structure, "class")
functions = analyzer.find_symbols_by_type(structure, "function")

print(f"Found {len(classes)} classes, {len(functions)} functions")

# Build dependency graph
graph = analyzer.get_symbol_graph(structure)
for symbol, info in graph.items():
    print(f"{symbol} depends on: {info['dependencies']}")
```

### Session Analysis

```python
from core import SessionAnalyzer, EventStore

store = EventStore()
analyzer = SessionAnalyzer(store)

# Analyze a session
context = analyzer.analyze_session("session-123")
print(f"Intent: {context.primary_intent}")
print(f"Workflow: {context.workflow_type}")
print(f"Success: {context.success_indicators}")

# Detect problem-solving patterns
patterns = analyzer.detect_problem_solving_patterns(lookback_days=30)
for pattern in patterns:
    print(f"{pattern.pattern_type}: {pattern.success_rate}")
```

### Design Pattern Detection

```python
from core import DesignPatternDetector, LSPAnalyzer
from pathlib import Path

lsp = LSPAnalyzer()
detector = DesignPatternDetector(lsp)

# Detect patterns in project
patterns = detector.detect_patterns_in_project(Path("/path/to/project"))

for pattern in patterns:
    print(f"{pattern.pattern_name} ({pattern.pattern_type})")
    print(f"Confidence: {pattern.confidence}")
    print(f"Indicators: {pattern.indicators}")

# Get pattern context (when/why/how)
context = detector.get_pattern_context("Repository")
print(f"When to use: {context.when_to_use}")
print(f"Benefits: {context.benefits}")
print(f"Trade-offs: {context.trade_offs}")
```

## 🔍 Privacy & Data

V2 respects your privacy:

- **Local Storage Only** - All data stored in `~/.claude/auto-skill/`
- **No Conversations Stored** - By default, only metadata (not full text)
- **Configurable** - Control what's analyzed via config
- **No External Services** - Everything runs locally

### Data Locations

- Events: `~/.claude/auto-skill/events.db` (SQLite)
- Sessions: `~/.claude/auto-skill/sessions/` (JSON metadata)
- Skills: `~/.claude/skills/auto/` (SKILL.md files)
- Config: `~/.claude/auto-skill.local.md`

### Cleanup

```python
from core import EventStore

store = EventStore()
# Delete events older than 30 days
deleted = store.cleanup_old_events(days=30)
print(f"Deleted {deleted} old events")
```

## 🧩 Backward Compatibility

- **V1 skills work unchanged** - Existing skills load normally
- **V2 optional** - Can disable V2 features via config
- **Graceful degradation** - If V2 dependencies unavailable, falls back to V1
- **No breaking changes** - V2 is purely additive

## 🛠️ Development

### Running Tests

```bash
pytest tests/ -v
```

### Project Structure

```
claude-auto-skill/
├── core/                # Core modules
│   ├── event_store.py
│   ├── pattern_detector.py (enhanced)
│   ├── skill_generator.py (enhanced)
│   ├── session_analyzer.py (new)
│   ├── lsp_analyzer.py (new)
│   └── design_pattern_detector.py (new)
├── commands/            # CLI commands
├── scripts/             # Utility scripts
├── tests/               # Unit tests
├── skills/              # Generated skills
└── README.md           # This file
```

## 📚 Learn More

- **V1 Documentation:** See git history for original implementation
- **V2 Enhancements:** See `DELIVERABLES.md` for detailed feature list
- **Implementation Plan:** See `V2_IMPLEMENTATION.md`
- **Planning Documents:** See `planning/V2_PLAN.md` (detailed V2 planning and architecture)

## 🙏 Credits

Built for [Claude Code](https://claude.ai/code) to make AI assistance more contextually aware.

## 📜 License

MIT

---

**Claude Auto-Skill v2** - Learn from your patterns, understand the context, apply with confidence.
