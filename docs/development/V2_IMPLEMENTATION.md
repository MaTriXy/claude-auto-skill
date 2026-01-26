# Claude Auto-Skill v2 Implementation Plan

> **Note:** Detailed planning documents are located in `planning/V2_PLAN.md` (gitignored)

## Status: In Progress

### Completed ✅
1. **New Core Modules Created:**
   - ✅ `core/session_analyzer.py` - Full session history analysis
   - ✅ `core/lsp_analyzer.py` - Language Server Protocol integration
   - ✅ `core/design_pattern_detector.py` - Design pattern recognition
   - ✅ Updated `requirements.txt` with LSP dependencies

### In Progress 🔄
2. **Base Infrastructure (Required):**
   - ⏳ `core/event_store.py` - Event storage (from v1)
   - ⏳ `core/pattern_detector.py` - Enhanced with v2 capabilities
   - ⏳ `core/skill_generator.py` - Enhanced with design pattern metadata
   - ⏳ `core/sequence_matcher.py` - Subsequence matching (from v1)
   - ⏳ `core/config.py` - Configuration management

### Remaining 📋
3. **CLI Commands:**
   - `commands/analyze-session.md` - Session history analysis
   - `commands/analyze-code.md` - LSP code analysis
   - `commands/detect-patterns.md` - Design pattern detection
   - Update existing commands for v2 features

4. **Scripts:**
   - `scripts/analyze_session.py` - Session analysis CLI
   - `scripts/analyze_code_structure.py` - LSP analysis CLI
   - `scripts/detect_design_patterns.py` - Pattern detection CLI
   - Update existing scripts

5. **Tests:**
   - `tests/test_session_analyzer.py`
   - `tests/test_lsp_analyzer.py`
   - `tests/test_design_pattern_detector.py`
   - Update existing tests

6. **Documentation:**
   - Update README.md with v2 features
   - Update SKILL.md format spec
   - Create migration guide

## V2 Feature Summary

### 1. Session History Analysis
- **Full conversation context** (not just tools)
- **Decision tracking** (what decisions were made)
- **Problem-solving patterns** (TDD, debugging, refactoring)
- **Success indicators** (what worked, what didn't)

### 2. LSP Integration
- **Code structure** analysis (classes, functions, modules)
- **Dependency** mapping (imports, relationships)
- **Type information** (where available)
- **Symbol relationships** (call graphs, inheritance)

### 3. Design Pattern Recognition
- **Architectural patterns** (MVC, Repository, Factory, etc.)
- **Coding patterns** (error handling, async, decorators)
- **Workflow patterns** (TDD, debug-cycle, refactor-safe)
- **Pattern context** (when to use, benefits, trade-offs)

### 4. Enhanced Skill Generation
Skills now include:
- **Contextual understanding** (why pattern works)
- **Code structure awareness** (when to apply)
- **Design pattern metadata** (architectural context)
- **Problem-solving approach** (workflow strategy)

## Enhanced SKILL.md Format

```yaml
---
name: search-and-edit-workflow-a1b2c3
description: Workflow that searches then edits
context: fork
agent: general-purpose
allowed-tools: Grep, Read, Edit

# V1 metadata
auto-generated: true
confidence: 0.85
pattern-id: a1b2c3

# V2 enhancements
session-analysis:
  primary-intent: refactor
  problem-domains: [authentication, api]
  workflow-type: Refactor-Safe
  success-rate: 0.92

design-patterns:
  - name: Repository
    confidence: 0.75
    indicators: [data_access, repository pattern detected]
  - name: Error-First-Handling
    confidence: 0.68

code-context:
  analyzed-files: 5
  primary-languages: [python]
  detected-symbols:
    classes: [UserRepository, AuthService]
    functions: [validate_user, authenticate]

problem-solving-approach:
  type: Refactor-Safe
  steps:
    - Read existing code to understand structure
    - Identify refactoring opportunities
    - Make incremental changes
    - Run tests after each change
  when-to-use: When improving code without changing behavior
---
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        OBSERVATION                           │
│  ┌──────────────┐                                            │
│  │ EventStore   │ Records tool events + session context      │
│  └──────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                        ANALYSIS                              │
│  ┌──────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ SessionAnalyzer  │  │  LSPAnalyzer    │  │  Pattern    │ │
│  │                  │  │                 │  │  Detector   │ │
│  │ • Conversations  │  │ • Code symbols  │  │             │ │
│  │ • Decisions      │  │ • Dependencies  │  │ • V1 Tools  │ │
│  │ • Workflows      │  │ • Type info     │  │ • V2 Design │ │
│  └──────────────────┘  └─────────────────┘  └─────────────┘ │
│           │                      │                   │       │
│           └──────────────────────┴───────────────────┘       │
│                                  │                           │
└──────────────────────────────────┼───────────────────────────┘
                                   ▼
┌─────────────────────────────────────────────────────────────┐
│              DESIGN PATTERN RECOGNITION                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  DesignPatternDetector                                 │  │
│  │                                                        │  │
│  │  • Architectural patterns (MVC, Repository)           │  │
│  │  • Coding patterns (Error handling, Async)            │  │
│  │  • Workflow patterns (TDD, Debug-cycle)               │  │
│  │  • Pattern contexts (when/why/how)                    │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    SKILL GENERATION                          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Enhanced SkillGenerator                               │  │
│  │                                                        │  │
│  │  Generates SKILL.md with:                              │  │
│  │  • Tool patterns (V1)                                  │  │
│  │  • Session context (V2)                                │  │
│  │  • Code structure insights (V2)                        │  │
│  │  • Design pattern metadata (V2)                        │  │
│  │  • Problem-solving approach (V2)                       │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Next Steps

Continue implementation in order:
1. Create base modules (event_store, sequence_matcher, config)
2. Create enhanced pattern_detector integrating v2 analyzers
3. Create enhanced skill_generator with v2 metadata
4. Add CLI commands
5. Add scripts
6. Write comprehensive tests
7. Update documentation

## Branch Strategy

- Branch: `v2-session-lsp-analysis`
- Keep v1 functionality intact
- All v2 features are additions, not replacements
- Backward compatible with v1 skills
