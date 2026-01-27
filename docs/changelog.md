# Changelog

All notable changes to Claude Auto-Skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Comprehensive documentation site with MkDocs Material
- GitHub Pages deployment workflow
- FAQ page with 40+ common questions
- Feature overview pages
- Getting started guides

---

## [2.0.0] - 2026-01-27

### Added - Priority 3 Features

- **Graduation System**: Automatic external→local skill promotion
  - Auto-detect graduation candidates (≥85%, ≥5 uses, ≥80% success)
  - Interactive approval workflow
  - Batch graduation mode
  - Complete graduation history tracking
  - CLI: `python -m core.graduation_manager`

- **Skills.sh Publishing**: Community skill sharing
  - Detect publishable skills (quality criteria)
  - Interactive publish workflow
  - Sync community stats (installs, ratings)
  - Track publish status
  - CLI: `python -m core.skillssh_publisher`

- **Web UI**: Visual interface for everything
  - Flask server with 8 REST API endpoints
  - Skill browser with search/filter
  - Real-time adoption dashboard
  - Animated confidence visualization
  - One-click graduation & publishing
  - Responsive design (desktop + mobile)
  - Run: `cd web && python app.py`

### Added - Priority 2 Features

- **PyPI Package**: Professional packaging (PEP 621)
  - CLI entry points: `auto-skill`, `auto-skill-discover`
  - Extras: `v2`, `dev`, `all`
  - Modern `pyproject.toml` format
  - Tool configuration (Black, MyPy, Pytest)

- **Migration System**: Schema versioning
  - Automatic migration detection
  - Rollback support
  - Transaction safety
  - EventStore & SkillTracker migrations
  - CLI: migrations run automatically

- **Test Expansion**: 50+ test cases
  - Edge case testing (empty data, corruption, boundaries)
  - Performance testing (1000+ events, 100+ sessions)
  - Migration testing (version tracking, rollback)
  - Test markers: `slow`, `integration`, `requires_mental`, `requires_network`

### Added - Priority 1 Features

- **Updated README**: Complete rewrite with hybrid features
  - Hybrid Integration overview
  - Mental Model integration details
  - Priority 3 features documentation
  - Comparison table
  - Quick start examples

- **Init Command**: Auto-setup tool
  - Creates directory structure
  - Generates config file
  - Checks optional dependencies
  - Provides next steps
  - CLI: `python -m commands.init`

- **JSON Output**: Scriptable CLI
  - All commands support `--json` flag
  - Structured output for automation
  - Compatible with jq and other tools
  - Example: `python -m commands.discover --json`

### Added - Hybrid Integration

- **Mental Model Integration**: First-of-its-kind
  - Domain/capability/aspect understanding
  - Pattern enhancement with Mental context
  - Skill suggestions by domain
  - Auto-detection of Mental CLI
  - Graceful degradation

- **Skills.sh Discovery**: External skill marketplace
  - Search 27,471+ community skills
  - Tag-based filtering
  - Install count tracking
  - API client with health checks

- **Confidence Evolution**: 50%→85% progression
  - External skills start at 50%
  - Proven skills reach 75%
  - Local skills at 85%
  - Expert skills at 100%
  - Success-based adjustments

- **Unified Discovery**: Multi-source suggestions
  - Combines Mental + Skills.sh + local patterns
  - Deduplication and ranking
  - Adoption tracking
  - Auto-graduation detection

### Added - V2 Features

- **Session Analysis**: Intent detection
  - 6 intent types: debug, implement, refactor, test, explore, document
  - 4 workflow types: TDD, Refactor-Safe, Debug-Systematic, Explore-Then-Implement
  - Problem domain extraction
  - Success indicators

- **LSP Integration**: Code structure analysis
  - Python AST parsing
  - Class/function/method extraction
  - Import graph analysis
  - Framework detection

- **Design Pattern Detection**: 18 patterns
  - 8 architectural patterns (MVC, Repository, Factory, etc.)
  - 6 coding patterns (Error handling, REST API, Async, etc.)
  - 4 workflow patterns (TDD, Refactor-Safe, etc.)

---

## [1.0.0] - 2025-12-15

### Added - Core Features

- **Pattern Detection**: Automatic workflow pattern discovery
  - Sequence matching algorithm
  - Min 3 occurrences threshold
  - Configurable sensitivity
  - SQLite event store

- **Skill Generation**: SKILL.md creation
  - YAML frontmatter with metadata
  - Tool sequence documentation
  - Usage instructions
  - Success indicators

- **Event Store**: SQLite-based logging
  - Tool call recording
  - Session tracking
  - Project context
  - Query interface

- **CLI Commands**: Basic command set
  - `run_detector.py`: Pattern detection
  - Configuration via Markdown files

---

## Version History

- **v2.0.0** (2026-01-27): Hybrid Integration + Priority 3 features
- **v1.2.0** (2026-01-20): V2 features (Session Analysis, LSP, Patterns)
- **v1.1.0** (2026-01-15): Skill tracking and confidence system
- **v1.0.0** (2025-12-15): Initial release

---

## Migration Guide

### From v1.x to v2.0

**Breaking Changes**: None (backward compatible)

**New Features**:

1. Run migrations (automatic):
   ```bash
   python -m core.migrations
   ```

2. Update config for new features:
   ```yaml
   hybrid:
     enable_mental: true
     enable_external: true
   ```

3. Install new dependencies:
   ```bash
   pip install -r requirements.txt
   ```

**Optional**:

- Install Mental CLI for enhanced context
- Install V2 dependencies for advanced features
- Try the Web UI: `cd web && python app.py`

---

## Roadmap

See [GitHub Issues](https://github.com/MaTriXy/claude-auto-skill/issues) for upcoming features.

**Planned**:

- [ ] Skill detail modal in Web UI
- [ ] Confidence history charts
- [ ] Mental Model visualization
- [ ] Multi-user support
- [ ] Real-time WebSocket updates
- [ ] Skill export/import
- [ ] Dark mode
- [ ] JavaScript/TypeScript LSP support
- [ ] Skills.sh real API integration (when available)
- [ ] PyPI publication

---

[Unreleased]: https://github.com/MaTriXy/claude-auto-skill/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/MaTriXy/claude-auto-skill/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/MaTriXy/claude-auto-skill/releases/tag/v1.0.0
