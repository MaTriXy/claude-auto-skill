# Claude Auto-Skill V2: System Flow Documentation

**Version:** 2.0.0  
**Date:** January 26, 2025  
**Purpose:** Comprehensive flow documentation of data and control through the system

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Data Flow: Tool Usage → Skill Generation](#data-flow-tool-usage--skill-generation)
3. [V2 Enhancement Flow](#v2-enhancement-flow)
4. [User Journey Walkthrough](#user-journey-walkthrough)
5. [API Flow: Key Function Calls](#api-flow-key-function-calls)
6. [Diagrams](#diagrams)

---

## Architecture Overview

### System Components

Claude Auto-Skill V2 consists of several interconnected modules that work together to observe, learn, and generate reusable skills:

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLAUDE AUTO-SKILL V2                          │
│                     System Architecture                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │   Hooks Layer  │  │  Core Modules  │  │  Commands Layer  │  │
│  ├────────────────┤  ├────────────────┤  ├──────────────────┤  │
│  │                │  │                │  │                  │  │
│  │ PostToolUse ───┼─▶│ EventStore     │◀─┤ /auto-skill:     │  │
│  │ Hook           │  │ ┌────────────┐ │  │   review         │  │
│  │                │  │ │  SQLite DB │ │  │   approve        │  │
│  │                │  │ └────────────┘ │  │   status         │  │
│  │                │  │                │  │   load           │  │
│  └────────────────┘  │ PatternDetector│◀─┤                  │  │
│                      │ ┌────────────┐ │  │                  │  │
│                      │ │ Sequence   │ │  │                  │  │
│                      │ │ Matcher    │ │  │                  │  │
│                      │ └────────────┘ │  │                  │  │
│                      │                │  │                  │  │
│                      │ V2 Analyzers:  │  │                  │  │
│                      │ ┌────────────┐ │  │                  │  │
│                      │ │ Session    │ │  │                  │  │
│                      │ │ Analyzer   │ │  │                  │  │
│                      │ ├────────────┤ │  │                  │  │
│                      │ │ LSP        │ │  │                  │  │
│                      │ │ Analyzer   │ │  │                  │  │
│                      │ ├────────────┤ │  │                  │  │
│                      │ │ Design     │ │  │                  │  │
│                      │ │ Pattern    │ │  │                  │  │
│                      │ │ Detector   │ │  │                  │  │
│                      │ └────────────┘ │  │                  │  │
│                      │                │  │                  │  │
│                      │ SkillGenerator │◀─┤                  │  │
│                      │ ┌────────────┐ │  │                  │  │
│                      │ │ SKILL.md   │ │  │                  │  │
│                      │ │ Templates  │ │  │                  │  │
│                      │ └────────────┘ │  │                  │  │
│                      └────────────────┘  └──────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Key Outputs |
|-----------|----------------|-------------|
| **PostToolUse Hook** | Captures tool usage in real-time | ToolEvent records |
| **EventStore** | Persists and queries tool events | Tool sequences |
| **SequenceMatcher** | Finds repeated subsequences | Common patterns |
| **PatternDetector (V1)** | Scores and ranks patterns | DetectedPattern (basic) |
| **SessionAnalyzer (V2)** | Analyzes conversation context | SessionContext |
| **LSPAnalyzer (V2)** | Parses code structure | CodeStructure |
| **DesignPatternDetector (V2)** | Identifies design patterns | DesignPattern |
| **PatternDetector (V2)** | Enriches patterns with V2 data | DetectedPattern (enhanced) |
| **SkillGenerator** | Creates SKILL.md files | Executable skills |
| **Command Handlers** | User-facing CLI interface | User interactions |

---

## Data Flow: Tool Usage → Skill Generation

### End-to-End Data Flow

```
USER ACTION                    OBSERVATION                  ANALYSIS                    GENERATION
     │                              │                           │                            │
     │  Claude uses tools           │                           │                            │
     │  (Read, Edit, Bash, etc.)    │                           │                            │
     ├──────────────────────────────▶                           │                            │
     │                              │                           │                            │
     │                         PostToolUse                      │                            │
     │                         Hook triggers                    │                            │
     │                              │                           │                            │
     │                         ToolEvent                        │                            │
     │                         created                          │                            │
     │                         {                                │                            │
     │                           tool_name: "Read"              │                            │
     │                           tool_input: {...}              │                            │
     │                           success: true                  │                            │
     │                           timestamp: ...                 │                            │
     │                         }                                │                            │
     │                              │                           │                            │
     │                              ├───────────────────────────▶                            │
     │                              │                           │                            │
     │                         EventStore                       │                            │
     │                         stores to DB                     │                            │
     │                         (SQLite)                         │                            │
     │                              │                           │                            │
     │                              │  [Pattern Detection       │                            │
     │                              │   runs periodically]      │                            │
     │                              │                           │                            │
     │                              ├───────────────────────────▶                            │
     │                              │                      Get sequences                     │
     │                              │                      (last N days)                     │
     │                              │                           │                            │
     │                              │                      SequenceMatcher                   │
     │                              │                      finds repeats                     │
     │                              │                           │                            │
     │                              │                      SequenceMatch                     │
     │                              │                      {                                 │
     │                              │                        sequence: [Read, Edit, Bash]   │
     │                              │                        occurrences: 5                 │
     │                              │                        session_indices: [0,2,4,...]   │
     │                              │                      }                                 │
     │                              │                           │                            │
     │                              │                      PatternDetector                   │
     │                              │                      enriches pattern                  │
     │                              │                           │                            │
     │                              │                      ┌─────────────┐                   │
     │                              │                      │ V2 Analysis │                   │
     │                              │                      └─────────────┘                   │
     │                              │                           │                            │
     │                              │                      SessionAnalyzer                   │
     │                              │                      - Primary intent                  │
     │                              │                      - Problem domains                 │
     │                              │                      - Workflow type                   │
     │                              │                           │                            │
     │                              │                      LSPAnalyzer                       │
     │                              │                      - Code structure                  │
     │                              │                      - Symbols, deps                   │
     │                              │                           │                            │
     │                              │                      DesignPatternDetector             │
     │                              │                      - Architectural patterns          │
     │                              │                      - Coding patterns                 │
     │                              │                           │                            │
     │                              │                      DetectedPattern                   │
     │                              │                      (V1 + V2 metadata)                │
     │                              │                           │                            │
     │                              │                           ├────────────────────────────▶
     │                              │                           │                            │
     │                              │                           │                      SkillGenerator
     │                              │                           │                      creates SKILL.md
     │                              │                           │                            │
     │  User reviews pattern        │                           │                      SkillCandidate
     │  via /auto-skill:review      │                           │                      {
     ◀────────────────────────────────────────────────────────────────────────────────   name: ...
     │                              │                           │                        description: ...
     │                              │                           │                        steps: [...]
     │  User approves pattern       │                           │                        v2_content: {...}
     │  /auto-skill:review          │                           │                      }
     │  approve abc123              │                           │                            │
     ├──────────────────────────────┼───────────────────────────┼────────────────────────────▶
     │                              │                           │                            │
     │                              │                           │                      SKILL.md written
     │                              │                           │                      to disk:
     │                              │                           │                      ~/.claude/skills/auto/
     │                              │                           │                      pattern-name-abc123/
     │  Skill loaded and ready      │                           │                      SKILL.md
     ◀────────────────────────────────────────────────────────────────────────────────────────┘
```

### Key Data Structures

#### 1. ToolEvent (EventStore)
```python
ToolEvent(
    tool_name="Read",
    tool_input={"path": "src/main.py"},
    tool_output="<file contents>",
    success=True,
    timestamp=datetime(...),
    session_id="session-abc123",
    project_path="/home/user/project"
)
```

#### 2. SequenceMatch (SequenceMatcher)
```python
SequenceMatch(
    sequence=('Read', 'Edit', 'Bash'),
    length=3,
    occurrences=5,
    session_indices=[0, 2, 4, 6, 9]
)
```

#### 3. DetectedPattern (PatternDetector)
```python
DetectedPattern(
    # V1 fields
    id="abc123def456",
    tool_sequence=['Read', 'Edit', 'Bash'],
    occurrence_count=5,
    confidence=0.85,
    session_ids=['session1', 'session2', ...],
    
    # V2 enhancements
    session_context={
        'primary_intent': 'refactor',
        'problem_domains': ['auth', 'api'],
        'workflow_type': 'Refactor-Safe',
        'tool_success_rate': 0.95
    },
    code_context={
        'analyzed_files': 15,
        'detected_symbols': {...},
        'dependencies': [...]
    },
    design_patterns=[
        {
            'name': 'Repository',
            'confidence': 0.75,
            'type': 'architectural'
        }
    ]
)
```

#### 4. SkillCandidate (SkillGenerator)
```python
SkillCandidate(
    name="read-edit-bash-workflow",
    description="Safe refactoring workflow",
    steps=[
        "1. Read the file to understand its contents",
        "2. Edit the file to make necessary changes",
        "3. Run tests to verify changes"
    ],
    yaml_frontmatter={
        'confidence': 0.85,
        'session-analysis': {...},
        'design-patterns': [...]
    },
    v2_content={
        'context_section': "...",
        'patterns_section': "..."
    }
)
```

---

## V2 Enhancement Flow

### How V2 Analyzers Enhance Pattern Detection

```
┌───────────────────────────────────────────────────────────────────────┐
│                    V2 ANALYSIS PIPELINE                                │
└───────────────────────────────────────────────────────────────────────┘

  DetectedPattern (V1 only)
         │
         │  Has: tool_sequence, confidence, occurrence_count
         │
         ▼
  ┌──────────────────┐
  │  V2 enabled?     │────NO───▶ Return pattern as-is (V1 compatible)
  └──────────────────┘
         │
         YES
         │
         ▼
  ╔══════════════════════════════════════════════════════════════╗
  ║              V2 ENHANCEMENT LAYER                             ║
  ╠══════════════════════════════════════════════════════════════╣
  ║                                                               ║
  ║  1. SESSION CONTEXT ANALYSIS                                  ║
  ║     ┌─────────────────────────────────────┐                  ║
  ║     │ SessionAnalyzer.analyze_session()   │                  ║
  ║     │                                     │                  ║
  ║     │ For each session_id in pattern:     │                  ║
  ║     │  • Parse conversation turns         │                  ║
  ║     │  • Detect primary intent            │                  ║
  ║     │  • Extract problem domains          │                  ║
  ║     │  • Identify workflow type           │                  ║
  ║     │  • Calculate success indicators     │                  ║
  ║     └─────────────────────────────────────┘                  ║
  ║                │                                              ║
  ║                ▼                                              ║
  ║     pattern.session_context = {                              ║
  ║       primary_intent: "refactor",                            ║
  ║       problem_domains: ["auth", "api"],                      ║
  ║       workflow_type: "Refactor-Safe",                        ║
  ║       tool_success_rate: 0.95                                ║
  ║     }                                                         ║
  ║                                                               ║
  ║  ──────────────────────────────────────────────────────────  ║
  ║                                                               ║
  ║  2. CODE STRUCTURE ANALYSIS                                   ║
  ║     ┌─────────────────────────────────────┐                  ║
  ║     │ LSPAnalyzer.analyze_project()       │                  ║
  ║     │                                     │                  ║
  ║     │ If project_path exists:             │                  ║
  ║     │  • Parse Python AST                 │                  ║
  ║     │  • Extract symbols (classes, funcs) │                  ║
  ║     │  • Build dependency graph           │                  ║
  ║     │  • Identify entry points            │                  ║
  ║     └─────────────────────────────────────┘                  ║
  ║                │                                              ║
  ║                ▼                                              ║
  ║     pattern.code_context = {                                 ║
  ║       analyzed_files: 15,                                    ║
  ║       detected_symbols: {                                    ║
  ║         classes: [{name: "UserAuth", ...}],                  ║
  ║         functions: [{name: "login", ...}]                    ║
  ║       },                                                      ║
  ║       dependencies: [...]                                    ║
  ║     }                                                         ║
  ║                                                               ║
  ║  ──────────────────────────────────────────────────────────  ║
  ║                                                               ║
  ║  3. DESIGN PATTERN DETECTION                                  ║
  ║     ┌─────────────────────────────────────┐                  ║
  ║     │ DesignPatternDetector                │                  ║
  ║     │                                     │                  ║
  ║     │ Workflow Patterns:                  │                  ║
  ║     │  • Check tool_sequence against      │                  ║
  ║     │    known workflow patterns          │                  ║
  ║     │  • Match TDD, Refactor-Safe, etc.   │                  ║
  ║     │                                     │                  ║
  ║     │ Code Patterns (if project exists):  │                  ║
  ║     │  • Scan code structure for:         │                  ║
  ║     │    - Architectural patterns (MVC)   │                  ║
  ║     │    - Coding patterns (async, REST)  │                  ║
  ║     │  • Calculate confidence scores      │                  ║
  ║     └─────────────────────────────────────┘                  ║
  ║                │                                              ║
  ║                ▼                                              ║
  ║     pattern.design_patterns = [                              ║
  ║       {                                                       ║
  ║         name: "Refactor-Safe",                               ║
  ║         type: "workflow",                                    ║
  ║         confidence: 0.85,                                    ║
  ║         indicators: ["Tool sequence: Read -> Edit -> Bash"]  ║
  ║       },                                                      ║
  ║       {                                                       ║
  ║         name: "Repository",                                  ║
  ║         type: "architectural",                               ║
  ║         confidence: 0.70,                                    ║
  ║         indicators: ["Found 'repository' in UserRepository"]║
  ║       }                                                       ║
  ║     ]                                                         ║
  ║                                                               ║
  ║  ──────────────────────────────────────────────────────────  ║
  ║                                                               ║
  ║  4. PROBLEM-SOLVING APPROACH                                  ║
  ║     ┌─────────────────────────────────────┐                  ║
  ║     │ If workflow_type detected:          │                  ║
  ║     │  • Lookup approach metadata         │                  ║
  ║     │  • Include when_to_use, steps       │                  ║
  ║     │  • Add benefits and trade-offs      │                  ║
  ║     └─────────────────────────────────────┘                  ║
  ║                │                                              ║
  ║                ▼                                              ║
  ║     pattern.problem_solving_approach = {                     ║
  ║       type: "Refactor-Safe",                                 ║
  ║       description: "Safe refactoring with tests",            ║
  ║       when_to_use: "When improving code structure...",       ║
  ║       steps: ["Read and understand...", ...],                ║
  ║       benefits: ["Maintains test coverage", ...]             ║
  ║     }                                                         ║
  ║                                                               ║
  ╚══════════════════════════════════════════════════════════════╝
         │
         ▼
  DetectedPattern (V1 + V2 enriched)
         │
         │  Now has: session_context, code_context,
         │           design_patterns, problem_solving_approach
         │
         ▼
  Passed to SkillGenerator
```

### V2 Enhancement Benefits

| Enhancement | What It Adds | Why It Matters |
|-------------|--------------|----------------|
| **Session Context** | User intent, problem domains, workflow type | Skills know *when* to be used |
| **Code Structure** | Classes, functions, dependencies | Skills understand *what* they're modifying |
| **Design Patterns** | Architectural & coding patterns | Skills follow best practices |
| **Problem-Solving** | Step-by-step approach | Skills teach *how* to solve problems |

---

## User Journey Walkthrough

### Journey 1: "I keep doing the same thing..."

```
┌──────────────────────────────────────────────────────────────────┐
│  DAY 1: User works on authentication refactoring                 │
└──────────────────────────────────────────────────────────────────┘

User: "Let's refactor the authentication module"

Claude:
  1. Reads auth/login.py              [PostToolUse hook captures]
  2. Edits auth/login.py              [PostToolUse hook captures]
  3. Runs pytest tests/test_auth.py   [PostToolUse hook captures]

EventStore now has: [Read, Edit, Bash] sequence, session-day1

┌──────────────────────────────────────────────────────────────────┐
│  DAY 2: User works on API endpoints                              │
└──────────────────────────────────────────────────────────────────┘

User: "Let's clean up the API endpoints"

Claude:
  1. Reads api/endpoints.py           [PostToolUse hook captures]
  2. Edits api/endpoints.py           [PostToolUse hook captures]
  3. Runs pytest tests/test_api.py    [PostToolUse hook captures]

EventStore now has: [Read, Edit, Bash] sequence, session-day2

┌──────────────────────────────────────────────────────────────────┐
│  DAY 3: User works on database layer                             │
└──────────────────────────────────────────────────────────────────┘

User: "Let's improve the database repository pattern"

Claude:
  1. Reads db/repository.py           [PostToolUse hook captures]
  2. Edits db/repository.py           [PostToolUse hook captures]
  3. Runs pytest tests/test_db.py     [PostToolUse hook captures]

EventStore now has: [Read, Edit, Bash] sequence, session-day3

┌──────────────────────────────────────────────────────────────────┐
│  BACKGROUND: Pattern detection runs (periodic or on-demand)       │
└──────────────────────────────────────────────────────────────────┘

PatternDetector.detect_patterns():
  1. Queries EventStore: "Get last 7 days of tool sequences"
  2. SequenceMatcher finds: [Read, Edit, Bash] appears 3 times
  3. Calculates confidence: 0.85 (high occurrence, recent, 100% success)
  
  V2 Enhancement:
  4. SessionAnalyzer: "Primary intent = refactor, domains = [auth, api, db]"
  5. LSPAnalyzer: "Project has 45 files, 12 classes, Repository pattern"
  6. DesignPatternDetector: "Detected: Refactor-Safe workflow (0.85)"

  Result: DetectedPattern with rich metadata

┌──────────────────────────────────────────────────────────────────┐
│  DAY 3 (continued): Claude offers to create skill                 │
└──────────────────────────────────────────────────────────────────┘

Claude: "I've noticed you frequently use this workflow:
         Read → Edit → Run Tests
         
         This appears to be a 'Refactor-Safe' pattern (85% confidence).
         Would you like me to create a reusable skill for this?
         
         /auto-skill:review to see details"

User: "/auto-skill:review"

Claude displays:
  ╔════════════════════════════════════════════════════════════╗
  ║  Detected Pattern: read-edit-bash-workflow (ID: abc123)    ║
  ╠════════════════════════════════════════════════════════════╣
  ║  Tool Sequence: Read → Edit → Bash                         ║
  ║  Confidence: 85%                                           ║
  ║  Occurrences: 3 times in last 7 days                       ║
  ║  Success Rate: 100%                                        ║
  ║                                                            ║
  ║  V2 Context:                                               ║
  ║  • Primary Intent: refactor                                ║
  ║  • Problem Domains: auth, api, db                          ║
  ║  • Workflow Type: Refactor-Safe                            ║
  ║  • Design Patterns: Repository (70%), Refactor-Safe (85%)  ║
  ║                                                            ║
  ║  Suggested Skill Name: refactor-safe-workflow              ║
  ║  Description: Safe refactoring with continuous testing     ║
  ║                                                            ║
  ║  To create: /auto-skill:review approve abc123             ║
  ╚════════════════════════════════════════════════════════════╝

User: "/auto-skill:review approve abc123"

SkillGenerator:
  1. Creates SkillCandidate with V2 metadata
  2. Generates SKILL.md with:
     - Context section (when to use this pattern)
     - Design patterns section (explains Repository, Refactor-Safe)
     - Code structure awareness (lists key classes/functions)
     - Problem-solving approach (step-by-step guide)
  3. Writes to ~/.claude/skills/auto/refactor-safe-workflow-abc123/SKILL.md
  4. Updates skill registry

Claude: "✅ Skill created: refactor-safe-workflow
         
         You can now use it with:
         /auto-skill:load refactor-safe-workflow
         
         Or I'll automatically suggest it when I detect similar contexts."

┌──────────────────────────────────────────────────────────────────┐
│  DAY 10: User starts similar refactoring task                    │
└──────────────────────────────────────────────────────────────────┘

User: "I need to refactor the payment processing module"

Claude: "I notice you're about to refactor code. You have a skill for this!
         
         📋 Skill: refactor-safe-workflow
         Context: Safe refactoring with continuous testing
         Best for: refactor tasks in codebases with good test coverage
         
         Would you like me to use this skill? (It will guide the process)"

User: "Yes, load it"

[Skill executes with enhanced context awareness]
```

### Journey 2: "Teach me best practices"

```
User: "/auto-skill:review"

Claude shows detected patterns, including design pattern insights:

Pattern: api-endpoint-workflow
• Design Patterns Detected:
  - REST-API-Design (confidence: 78%)
  - Error-First-Handling (confidence: 65%)
  - Repository (confidence: 72%)

• When to Use:
  When building REST APIs with proper error handling and data access abstraction

• Code Structure Detected:
  Classes: UserController, AuthRepository
  Functions: handle_login, validate_token
  
• Problem-Solving Approach:
  1. Design endpoint interface first
  2. Implement error handling
  3. Add repository layer
  4. Write integration tests
  5. Test error cases

User learns best practices embedded in their own workflow!
```

---

## API Flow: Key Function Calls

### Pattern Detection Flow

```python
# Entry point: User runs /auto-skill:review
def handle_review_command():
    detector = PatternDetector(store, enable_v2=True, project_path="/path/to/project")
    
    # 1. Detect patterns
    patterns = detector.detect_patterns(
        project_path="/path/to/project",
        min_occurrences=3,
        min_sequence_length=2,
        max_sequence_length=10,
        lookback_days=7
    )
    # Returns: list[DetectedPattern] with V1 + V2 metadata
    
    # 2. Filter by confidence
    high_confidence = [p for p in patterns if p.confidence >= 0.7]
    
    # 3. Display to user
    for pattern in high_confidence:
        display_pattern(pattern)  # Shows V2 context, design patterns, etc.
```

#### Internal Flow of `detect_patterns()`

```python
def detect_patterns(self, ...):
    # V1: Get tool sequences from EventStore
    sequences = self.store.get_tool_sequences(project_path, lookback_days, ...)
    # Returns: list[list[ToolEvent]]
    
    # V1: Find common subsequences
    matcher = SequenceMatcher(min_length, max_length, min_occurrences)
    matches = matcher.find_common_subsequences(sequences)
    # Returns: list[SequenceMatch]
    
    # V1: Get full event data
    event_sessions = self.store.get_events_with_inputs(project_path, lookback_days)
    
    # V1 + V2: Create DetectedPattern for each match
    patterns = []
    for match in matches:
        # V1: Basic pattern creation
        pattern = self._create_pattern(match, event_sessions, project_path)
        
        # V2: Enhancement happens inside _create_pattern
        if self.enable_v2:
            pattern = self._enhance_with_v2(pattern, session_ids, project_path)
            #  ▲ This is where magic happens!
        
        patterns.append(pattern)
    
    # Sort by confidence and return
    return sorted(patterns, key=lambda p: -p.confidence)
```

#### Inside `_enhance_with_v2()`

```python
def _enhance_with_v2(self, pattern, session_ids, project_path):
    # 1. Session Context
    if self.session_analyzer:
        contexts = [
            self.session_analyzer.analyze_session(sid)
            for sid in session_ids[:5]  # Sample first 5
        ]
        pattern.session_context = self._aggregate_contexts(contexts)
    
    # 2. Code Structure
    if self.lsp_analyzer and project_path:
        structure = self.lsp_analyzer.analyze_project(Path(project_path))
        pattern.code_context = {
            'analyzed_files': len(structure.symbols),
            'detected_symbols': {...},
            'dependencies': [...]
        }
    
    # 3. Design Patterns
    if self.design_pattern_detector:
        # Workflow pattern
        workflow = self.design_pattern_detector.detect_workflow_pattern(
            pattern.tool_sequence,
            pattern.session_context
        )
        
        # Code patterns (if project exists)
        if project_path:
            code_patterns = self.design_pattern_detector.detect_patterns_in_project(
                Path(project_path)
            )
        
        pattern.design_patterns = [workflow] + code_patterns[:3]
    
    # 4. Problem-Solving Approach
    if pattern.session_context.get('workflow_type'):
        pattern.problem_solving_approach = self._create_problem_solving_approach(
            pattern.session_context['workflow_type']
        )
    
    return pattern
```

### Skill Generation Flow

```python
# Entry point: User approves pattern
def handle_approve_command(pattern_id):
    # 1. Get the pattern
    patterns = detector.detect_patterns(...)
    pattern = next(p for p in patterns if p.id == pattern_id)
    
    # 2. Generate skill candidate
    generator = SkillGenerator()
    candidate = generator.generate_candidate(pattern)
    # Returns: SkillCandidate with V2 content
    
    # 3. Save to disk
    skill_path = generator.save_skill(candidate, update_registry=True)
    # Writes: ~/.claude/skills/auto/{name}/SKILL.md
    
    return skill_path
```

#### Internal Flow of `generate_candidate()`

```python
def generate_candidate(self, pattern):
    # V1: Basic skill metadata
    name = self._generate_skill_name(pattern)
    description = self._generate_description(pattern)
    steps = self._generate_steps(pattern)
    
    # V1: Execution context
    use_fork = self._should_use_fork(pattern.tool_sequence)
    agent_type = self._determine_agent_type(pattern.tool_sequence)
    allowed_tools = self._generate_allowed_tools(pattern.tool_sequence)
    
    # V1: YAML frontmatter
    frontmatter = self._build_frontmatter(
        pattern, name, description, use_fork, agent_type, allowed_tools
    )
    
    # V2: Enhanced content sections
    v2_content = None
    if hasattr(pattern, 'session_context'):
        v2_content = self._build_v2_content(pattern)
        # Includes:
        # - context_section: When to use this pattern
        # - patterns_section: Design patterns explanation
        # - code_structure_section: Key symbols and dependencies
        # - enhanced_steps: Problem-solving approach steps
    
    return SkillCandidate(
        pattern=pattern,
        name=name,
        description=description,
        steps=steps,
        yaml_frontmatter=frontmatter,
        v2_content=v2_content,
        ...
    )
```

---

## Diagrams

### Diagram 1: Component Interaction

```
                                    ┌────────────────┐
                                    │  Claude Code   │
                                    │   (user + AI)  │
                                    └────────┬───────┘
                                             │
                                     Uses tools (Read, Edit, ...)
                                             │
                                             ▼
                                    ┌────────────────┐
                                    │ PostToolUse    │
                                    │ Hook           │
                                    └────────┬───────┘
                                             │
                                     Creates ToolEvent
                                             │
                                             ▼
                    ┌────────────────────────────────────────────┐
                    │           EventStore (SQLite)              │
                    │  ┌──────────────────────────────────────┐  │
                    │  │  tool_events table                   │  │
                    │  │  ├─ tool_name                        │  │
                    │  │  ├─ tool_input (JSON)                │  │
                    │  │  ├─ tool_output (JSON)               │  │
                    │  │  ├─ success (bool)                   │  │
                    │  │  ├─ timestamp                        │  │
                    │  │  ├─ session_id                       │  │
                    │  │  └─ project_path                     │  │
                    │  └──────────────────────────────────────┘  │
                    └────────┬───────────────────────────────────┘
                             │
                     Queries for sequences
                             │
                             ▼
        ┌────────────────────────────────────────────────┐
        │         PatternDetector (V1 + V2)              │
        │                                                 │
        │  ┌──────────────────────────────────────────┐  │
        │  │  V1 Core                                 │  │
        │  │  • Get sequences from EventStore         │  │
        │  │  • SequenceMatcher finds repeats         │  │
        │  │  • Calculate confidence scores           │  │
        │  └──────────────────────────────────────────┘  │
        │                     │                           │
        │                     ▼                           │
        │  ┌──────────────────────────────────────────┐  │
        │  │  V2 Enhancement Layer                    │  │
        │  │  ┌────────────────────────────────────┐  │  │
        │  │  │  SessionAnalyzer                   │  │  │
        │  │  │  • Analyze conversation context    │  │  │
        │  │  │  • Detect intents, domains         │  │  │
        │  │  └────────────────────────────────────┘  │  │
        │  │  ┌────────────────────────────────────┐  │  │
        │  │  │  LSPAnalyzer                       │  │  │
        │  │  │  • Parse code structure (AST)      │  │  │
        │  │  │  • Extract symbols, dependencies   │  │  │
        │  │  └────────────────────────────────────┘  │  │
        │  │  ┌────────────────────────────────────┐  │  │
        │  │  │  DesignPatternDetector             │  │  │
        │  │  │  • Detect architectural patterns   │  │  │
        │  │  │  • Identify workflow patterns      │  │  │
        │  │  └────────────────────────────────────┘  │  │
        │  └──────────────────────────────────────────┘  │
        │                     │                           │
        │                     ▼                           │
        │          DetectedPattern (enriched)             │
        └────────────────────┬────────────────────────────┘
                             │
                     Passed to generator
                             │
                             ▼
                    ┌────────────────┐
                    │ SkillGenerator │
                    │                │
                    │ Renders:       │
                    │ • V1 metadata  │
                    │ • V2 sections  │
                    │ • YAML front   │
                    └────────┬───────┘
                             │
                     Writes SKILL.md
                             │
                             ▼
                    ┌────────────────┐
                    │  File System   │
                    │  ~/.claude/    │
                    │   skills/auto/ │
                    └────────────────┘
```

### Diagram 2: V2 Analysis Pipeline

```
DetectedPattern (V1 only)
         │
         │ tool_sequence: [Read, Edit, Bash]
         │ confidence: 0.85
         │ occurrence_count: 5
         │
         ▼
    ╔═══════════════════════════════════════════════════╗
    ║        V2 ENHANCEMENT (if enabled)                ║
    ╚═══════════════════════════════════════════════════╝
         │
         ├──────────────────────────────────────────┐
         │                                          │
         ▼                                          ▼
    ┌────────────────┐                    ┌────────────────┐
    │ SessionAnalyzer│                    │  LSPAnalyzer   │
    │                │                    │                │
    │ For sessions:  │                    │ For project:   │
    │ • Parse turns  │                    │ • Parse AST    │
    │ • Detect       │                    │ • Extract      │
    │   intents      │                    │   symbols      │
    │ • Extract      │                    │ • Build dep    │
    │   domains      │                    │   graph        │
    │ • Identify     │                    │                │
    │   workflow     │                    │                │
    └────────┬───────┘                    └────────┬───────┘
             │                                     │
             │ session_context                     │ code_context
             │  {                                  │  {
             │    primary_intent: "refactor",      │    analyzed_files: 15,
             │    problem_domains: ["auth"],       │    symbols: {...},
             │    workflow_type: "Refactor-Safe"   │    dependencies: [...]
             │  }                                  │  }
             │                                     │
             └──────────────┬──────────────────────┘
                            │
                            ▼
                   ┌─────────────────────┐
                   │DesignPatternDetector│
                   │                     │
                   │ Combines:           │
                   │ • Workflow pattern  │
                   │   from tool seq     │
                   │ • Code patterns     │
                   │   from structure    │
                   └──────────┬──────────┘
                              │
                              │ design_patterns: [...]
                              │ problem_solving_approach: {...}
                              │
                              ▼
                DetectedPattern (V1 + V2 enriched)
                       │
                       │ NOW HAS:
                       │ • session_context
                       │ • code_context
                       │ • design_patterns
                       │ • problem_solving_approach
                       │
                       ▼
                 Ready for skill generation!
```

### Diagram 3: Skill Generation with V2 Content

```
SkillGenerator.generate_candidate(pattern)
         │
         ├─── V1 Content Generation
         │    │
         │    ├─ name = _generate_skill_name()
         │    ├─ description = _generate_description()
         │    ├─ steps = _generate_steps()
         │    ├─ use_fork = _should_use_fork()
         │    └─ frontmatter = _build_frontmatter()
         │
         └─── V2 Content Generation (if pattern has V2 data)
              │
              ├─ _build_context_section()
              │  ▼
              │  ## Context
              │  This workflow is most appropriate when:
              │  - You are refactoring
              │  - Working in areas: auth, api
              │  - Following a Refactor-Safe approach
              │
              ├─ _build_patterns_section()
              │  ▼
              │  ## Detected Patterns
              │  ### Refactor-Safe (workflow, 85% confidence)
              │  - Description: Safe refactoring with continuous testing
              │  - When to use: Improving code structure without changing behavior
              │  - Benefits: Maintains test coverage, Reduces risk
              │
              ├─ _build_code_structure_section()
              │  ▼
              │  ## Code Structure Awareness
              │  **Key Classes:**
              │  - `UserAuth` (auth/user.py:15)
              │  - `AuthRepository` (db/repository.py:42)
              │
              └─ _build_enhanced_steps()
                 ▼
                 1. Read and understand the current implementation (Read)
                 2. Identify code smells and refactoring opportunities
                 3. Make small, incremental changes (Edit)
                 4. Run tests after each change (Bash)
         │
         ▼
SKILL.md with V1 + V2 content:

---
name: refactor-safe-workflow-abc123
description: Safe refactoring workflow
confidence: 0.85
session-analysis: {...}
design-patterns: [...]
---

# refactor-safe-workflow-abc123

Safe refactoring with continuous testing

## Context
[V2: When to use this pattern]

## Detected Patterns
[V2: Design patterns explanation]

## Steps
[V1 + V2 enhanced steps]

## Code Structure Awareness
[V2: Key classes, functions, dependencies]

## Generated by Claude Auto-Skill v2
```

---

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|------------|-------|
| PostToolUse hook | O(1) | Single DB insert |
| Pattern detection (V1) | O(n²) | Subsequence matching across n sequences |
| Session analysis | O(s × t) | s sessions, t turns per session |
| LSP analysis | O(f × l) | f files, l lines per file (AST parsing) |
| Design pattern detection | O(p × i) | p patterns, i indicators |
| Skill generation | O(1) | Template rendering is fast |

### Space Complexity

| Component | Storage | Growth Rate |
|-----------|---------|-------------|
| EventStore (SQLite) | ~1KB per tool event | Linear with usage |
| Session analysis cache | ~5KB per session | Linear with sessions analyzed |
| LSP CodeStructure | ~10KB per project | Linear with project size |
| Generated skills | ~5KB per skill | Linear with approved patterns |

### Optimization Strategies

1. **Lazy Loading:** V2 analyzers only initialized when needed
2. **Sampling:** Session analysis samples first 5 sessions (not all)
3. **Caching:** File content cached during pattern detection
4. **Indexing:** SQLite indexes on session_id, project_path, timestamp

---

## Error Handling & Edge Cases

### Graceful Degradation

```
V2 Feature Unavailable
         │
         ├─ LSP dependencies missing
         │  └─ Falls back to V1 pattern detection (no code analysis)
         │
         ├─ Project path invalid
         │  └─ Skips code structure analysis, continues with session analysis
         │
         ├─ Session data missing
         │  └─ Uses tool sequences only, generates basic skill
         │
         └─ Parse error in code
            └─ Logs warning, continues with other files
```

### Error Recovery

- **DB corruption:** Recreates EventStore from backup
- **Skill generation fails:** Returns error, doesn't corrupt existing skills
- **Pattern detection crash:** Returns empty list, doesn't affect EventStore

---

## Conclusion

Claude Auto-Skill V2's architecture demonstrates:

1. **Clean Separation:** V1 and V2 features are decoupled yet integrated
2. **Progressive Enhancement:** V2 enriches V1 without replacing it
3. **Extensibility:** New analyzers can be added without modifying core
4. **Performance Awareness:** Lazy loading, sampling, and caching used strategically
5. **User-Centric Design:** Rich metadata helps users understand *why* patterns matter

The flow from tool usage → pattern detection → skill generation is transparent, debuggable, and produces actionable results that genuinely improve developer productivity.

---

**Document Version:** 1.0  
**Last Updated:** January 26, 2025  
**Author:** Claude Auto-Skill V2 Development Team
