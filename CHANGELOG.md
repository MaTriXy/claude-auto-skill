# Changelog

All notable changes to Claude Auto-Skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2025-01-26

### 🎉 Major Release: V2 - Session Analysis, LSP Integration & Design Patterns

Claude Auto-Skill V2 is a **major enhancement** that transforms the plugin from a simple pattern detector into an intelligent learning system. V2 adds context awareness, code structure understanding, and design pattern recognition while maintaining **100% backward compatibility** with V1.

### ✨ Added

#### Session Analysis (New Module)
- **Full conversation context analysis** - Understands user intents and problem domains
- **Intent detection** - Categorizes sessions into: debug, implement, refactor, test, explore, document
- **Problem domain extraction** - Identifies areas of work (auth, api, database, etc.)
- **Workflow type identification** - Detects TDD, Refactor-Safe, Debug-Systematic, Explore-Then-Implement
- **Success indicators** - Calculates tool success rates and session metrics
- **Problem-solving pattern detection** - Identifies high-level approaches across sessions
- **New file:** `core/session_analyzer.py` (422 lines)

#### LSP Integration (New Module)
- **Python AST analysis** - Complete code structure parsing
- **Symbol extraction** - Classes, functions, methods, decorators
- **Dependency tracking** - Import graphs and module relationships
- **Entry point detection** - Identifies main functions and CLI commands
- **Multi-language framework** - Ready for JS/TS (basic regex fallback)
- **Symbol search** - Find symbols by type, name pattern, or file
- **Dependency trees** - Build hierarchical dependency graphs
- **New file:** `core/lsp_analyzer.py` (408 lines)

#### Design Pattern Detection (New Module)
- **Architectural patterns** (8 patterns):
  - MVC, Repository, Factory, Singleton, Strategy, Observer, Adapter, Dependency-Injection
- **Coding patterns** (6 patterns):
  - Error-First-Handling, REST-API-Design, Async-Pattern, Decorator-Pattern, Context-Manager, Builder-Pattern
- **Workflow patterns** (4 patterns):
  - TDD, Refactor-Safe, Debug-Systematic, Explore-Then-Implement
- **Confidence scoring** - Statistical confidence for each detected pattern
- **Pattern context** - When to use, benefits, trade-offs for each pattern
- **Pattern suggestions** - Recommends patterns based on intent and domain
- **New file:** `core/design_pattern_detector.py` (471 lines)

#### Enhanced Pattern Detection
- **V2 enhancement layer** - Enriches V1 patterns with V2 metadata
- **Session context integration** - Adds user intent and workflow type to patterns
- **Code context integration** - Includes project structure in patterns
- **Design pattern metadata** - Lists detected patterns with confidence scores
- **Problem-solving approaches** - Documents methodology for each workflow
- **Feature flag** - `enable_v2` parameter for opt-in/opt-out
- **Graceful degradation** - Falls back to V1 if V2 dependencies missing
- **Enhanced file:** `core/pattern_detector.py` (now 588 lines, was 158)

#### Enhanced Skill Generation
- **Context sections** - Explains when and why to use each skill
- **Design patterns sections** - Documents patterns with guidance
- **Code structure awareness** - Lists relevant classes, functions, dependencies
- **Problem-solving approaches** - Step-by-step methodology for workflows
- **Rich YAML frontmatter** - All V2 metadata included for introspection
- **Enhanced steps** - Uses problem-solving approach steps when available
- **V2 content builder** - Modular content generation for each section
- **Enhanced file:** `core/skill_generator.py` (complete rewrite, 523 lines)

#### Testing
- **V2 integration tests** - Comprehensive test suite for V2 features
- **Session analysis tests** - Mock conversation data and intent detection
- **LSP analysis tests** - Python project parsing and symbol extraction
- **Design pattern tests** - Pattern detection and confidence scoring
- **Skill generation tests** - V2 content rendering validation
- **New file:** `tests/test_v2_integration.py` (360 lines)

#### Documentation
- **V2 feature overview** - Complete guide to V2 capabilities (`README_V2.md`, 527 lines)
- **Implementation details** - Technical documentation (`V2_IMPLEMENTATION.md`, 189 lines)
- **Completion summary** - Development tracking (`V2_COMPLETION_SUMMARY.md`, 622 lines)
- **Code review** - Comprehensive review findings (`REVIEW.md`)
- **Flow documentation** - System architecture and data flow (`FLOW.md`)
- **PR description** - Detailed pull request documentation (`PR_DESCRIPTION.md`)
- **Enhanced README** - Added V2 overview section to main README

#### Dependencies
- **LSP support:** `pygls>=1.3.0`
- **Tree-sitter:** `tree-sitter>=0.21.0` (framework, not yet utilized)
- **Tree-sitter parsers:** Python, JavaScript, TypeScript language parsers
- **Pattern recognition:** `numpy>=1.24.0`, `scikit-learn>=1.3.0`
- **Testing:** `pytest>=7.0` (now in requirements.txt)

### 🔄 Changed

- **PatternDetector** - Enhanced to support V2 analyzers (lazy-loaded, optional)
- **SkillGenerator** - Complete rewrite with V2 content generation
- **DetectedPattern dataclass** - Extended with V2 fields (session_context, code_context, design_patterns, problem_solving_approach)
- **SkillCandidate dataclass** - Added v2_content field for enhanced sections
- **SKILL.md template** - Now includes context, patterns, and code structure sections

### 🛡️ Security

- **Path validation** - Proper use of `Path` objects throughout
- **YAML safety** - Uses `yaml.safe_dump()` to prevent injection
- **Input sanitization** - Added validation for file paths (some areas still need improvement)

### 🔧 Fixed

- **pytest dependency** - Added to requirements.txt for test execution
- **Import paths** - Consistent relative imports across modules
- **Error handling** - Improved exception handling in V2 modules (still needs work in some areas)

### 📝 Notes

#### Backward Compatibility
**100% backward compatible** - No breaking changes:
- V1 API completely unchanged
- V2 features are additive only
- Feature flag (`enable_v2`) controls V2 activation
- Graceful degradation if V2 dependencies missing

#### Known Limitations
- **Tree-sitter integration**: Framework present but not implemented (Python AST works fully)
- **Pattern contexts**: Only 3/14 patterns have complete context documentation
- **Conversation parsing**: Uses tool events as proxy (full conversation log integration pending)
- **JS/TS support**: Basic regex fallback only (AST parsing not implemented)

#### Migration Guide
**No migration required** - V2 is a drop-in enhancement:
1. Update plugin: `git pull origin main`
2. Install dependencies: `pip install -r requirements.txt` (optional)
3. V2 features activate automatically

### 📊 Statistics

- **Files changed:** 21
- **Lines added:** 5,558
- **Lines removed:** 417
- **Net change:** +5,141 lines
- **Core modules added:** 3 (session_analyzer, lsp_analyzer, design_pattern_detector)
- **Core modules enhanced:** 2 (pattern_detector, skill_generator)
- **Test coverage:** 5 test modules (4 V1 + 1 V2)
- **Documentation added:** 6 comprehensive documents

---

## [1.0.0] - 2024-XX-XX

### 🎉 Initial Release: V1 - Auto-Detection and Skill Generation

The first version of Claude Auto-Skill, providing automatic workflow learning from Claude Code sessions.

### ✨ Added

#### Core Features
- **PostToolUse Hook** - Captures tool usage in real-time
- **EventStore** - SQLite database for persistent tool event storage
- **SequenceMatcher** - Finds repeated subsequences across sessions
- **PatternDetector** - Scores and ranks patterns by confidence
- **SkillGenerator** - Creates SKILL.md files from patterns
- **Command handlers** - CLI interface for user interactions

#### Pattern Detection (V1)
- **Tool sequence detection** - Identifies repeated tool usage patterns
- **Confidence scoring** - Multi-factor scoring algorithm:
  - Occurrence frequency (40%)
  - Sequence length (20%)
  - Success rate (25%)
  - Recency (15%)
- **Pattern ID generation** - Unique identifiers for patterns
- **Session tracking** - Links patterns to originating sessions

#### Skill Generation (V1)
- **SKILL.md creation** - Markdown format with YAML frontmatter
- **Step generation** - Procedural steps from tool sequences
- **Execution context** - Fork detection and agent type hints
- **Tool restrictions** - `allowed-tools` list for security
- **Metadata inclusion** - Confidence, occurrence count, session IDs

#### Commands
- `/auto-skill:review` - List detected patterns
- `/auto-skill:review approve ID` - Create skill from pattern
- `/auto-skill:load <name>` - Load skill mid-session
- `/auto-skill:status` - Show system statistics

#### Event Storage
- **SQLite backend** - Lightweight, file-based storage
- **Event fields** - tool_name, tool_input, tool_output, success, timestamp, session_id, project_path
- **Query methods** - Get sequences by project, session, time range
- **Indexing** - Optimized queries on session_id, project_path, timestamp

#### Testing
- `test_event_store.py` - EventStore CRUD operations
- `test_sequence_matcher.py` - Subsequence matching algorithms
- `test_pattern_detector.py` - Pattern detection and scoring
- `test_skill_generator.py` - SKILL.md generation

#### Documentation
- **README.md** - Complete user guide with examples
- **Inline docstrings** - All public methods documented
- **Architecture diagrams** - ASCII art showing data flow

### 🛡️ Security

- **Tool restrictions** - Skills limited to detected tools only
- **Fork isolation** - Risky operations run in subagents
- **Local-only storage** - No external data transmission

### 📝 Notes

#### Design Principles (V1)
- **Observe, don't intervene** - Passive learning from natural usage
- **High confidence threshold** - Only suggest well-validated patterns
- **User approval required** - No automatic skill creation
- **Lightweight** - Minimal dependencies (PyYAML only)

#### V1 Limitations
- **No context awareness** - Only sees tool sequences, not user intent
- **No code understanding** - Treats code as opaque black boxes
- **No pattern recognition** - Can't identify design patterns or best practices
- **Generic skills** - Skills lack contextual guidance

**→ These limitations are addressed in V2.0.0**

---

## [Unreleased]

### 🚧 Planned for Future Releases

#### V2.1 (Planned)
- Complete pattern context documentation (11 remaining patterns)
- Structured logging throughout all modules
- Enhanced error handling and recovery
- Performance benchmarks and optimization
- LSP analysis caching for repeated pattern detection

#### V2.2 (Planned)
- Full conversation log integration (beyond tool events)
- Tree-sitter implementation for JS/TS
- Enhanced intent detection with NLP
- Pattern suggestion refinement
- Multi-project pattern sharing

#### V2.3 (Planned)
- Visual pattern explorer (web UI)
- Pattern analytics dashboard
- Team skill sharing and collaboration
- Cloud-based pattern repository (opt-in)

### 💡 Ideas Under Consideration
- **Active learning** - Ask clarifying questions during pattern detection
- **Pattern evolution** - Track how patterns change over time
- **Skill composition** - Combine multiple skills into workflows
- **Language-specific patterns** - Python/JS/TS-specific detection
- **Framework detection** - Identify Flask, Django, React, etc.
- **Anti-pattern detection** - Warn about problematic patterns

---

## Version History Summary

| Version | Release Date | Key Features | Status |
|---------|--------------|--------------|--------|
| **2.0.0** | 2025-01-26 | Session analysis, LSP, design patterns | ✅ Current |
| **1.0.0** | 2024-XX-XX | Auto-detection, skill generation | ✅ Stable |

---

## Contributing

We welcome contributions! Key areas for improvement:
- Complete pattern context documentation
- Implement tree-sitter for JS/TS
- Add structured logging
- Enhance error handling
- Write more tests

See `CONTRIBUTING.md` (if exists) or open an issue to discuss.

---

## License

See `LICENSE` file for details.

---

*Changelog maintained according to [Keep a Changelog](https://keepachangelog.com/) format*  
*Last updated: January 26, 2025*
