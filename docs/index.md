# Claude Auto-Skill 🦦

<div align="center">

![Claude Auto-Skill Banner](assets/banner.png)

**Automatically learn from your workflows and turn them into intelligent, context-aware skills.**

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/MaTriXy/claude-auto-skill/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-green.svg)](https://python.org)
[![GitHub Stars](https://img.shields.io/github/stars/MaTriXy/claude-auto-skill?style=social)](https://github.com/MaTriXy/claude-auto-skill)

</div>

---

## 🎯 What is Claude Auto-Skill?

Claude Auto-Skill observes your Claude Code sessions, detects repeated patterns, and generates reusable skills with deep contextual understanding. **Version 2.0 + Hybrid Integration** combines local pattern detection with external skill discovery and Mental Model understanding.

<div class="grid cards" markdown>

-   :material-brain: **Smart Learning**

    ---

    Automatically detects patterns from your workflow. No manual skill creation needed.

    [:octicons-arrow-right-24: Pattern Detection](features/pattern-detection.md)

-   :material-chart-line: **Confidence Evolution**

    ---

    Skills start at 50% confidence and evolve to 85%+ based on proven success.

    [:octicons-arrow-right-24: Graduation System](features/graduation.md)

-   :material-lightbulb: **Mental Model Integration**

    ---

    First-of-its-kind integration with Mental CLI for domain-aware skills.

    [:octicons-arrow-right-24: Mental Model](features/mental-model.md)

-   :material-web: **Beautiful Web UI**

    ---

    Visual skill browser, adoption dashboard, and one-click management.

    [:octicons-arrow-right-24: Web UI](features/web-ui.md)

</div>

## ✨ Key Features

### 🧠 V2 Core Features

- **Session Analysis**: Detects user intent (debug, implement, refactor, test, explore, document)
- **LSP Integration**: Python AST analysis for complete code structure understanding
- **Design Pattern Detection**: Identifies 18 patterns (architectural, coding, workflow)

### 🔄 Hybrid Integration

- **Mental Model**: Domain/capability/aspect understanding for semantic context
- **Skills.sh Discovery**: Access 27,471+ community skills from skills.sh
- **Confidence Evolution**: External skills (50%) → Proven (75%) → Local (85%)

### 🎓 Advanced Features

- **Automatic Graduation**: Promote proven external skills to trusted local skills
- **Skills.sh Publishing**: One-command publishing with community adoption tracking
- **Web UI**: Visual interface for browsing, managing, and analyzing skills

## 🚀 Quick Start

=== "Installation"

    ```bash
    # Clone repository
    git clone https://github.com/MaTriXy/claude-auto-skill.git
    cd claude-auto-skill

    # Install dependencies
    pip install -r requirements.txt

    # Initialize
    python -m commands.init
    ```

=== "Basic Usage"

    ```bash
    # Discover skills from your project
    python -m commands.discover

    # Generate skills
    python run_detector.py

    # Start web UI
    cd web && python app.py
    ```

=== "With Mental Model"

    ```bash
    # Install Mental CLI
    npm install -g @mental-model/cli

    # Add domains to your project
    mental add domain "Payment"
    mental add capability "Checkout"

    # Discover with Mental context
    python -m commands.discover --domain Payment
    ```

[Get Started →](getting-started/installation.md){ .md-button .md-button--primary }
[View on GitHub →](https://github.com/MaTriXy/claude-auto-skill){ .md-button }

## 📊 Comparison

| Feature | Auto-Skill | Vercel Skills | Manual |
|---------|-----------|---------------|--------|
| **Local Pattern Detection** | ✅ Automatic | ❌ None | ❌ Manual |
| **Mental Model Integration** | ✅ First-of-its-kind | ❌ None | ❌ None |
| **External Skill Discovery** | ✅ Skills.sh | ✅ Skills.sh | ❌ None |
| **Confidence Evolution** | ✅ 50% → 85% | ❌ None | ❌ None |
| **Auto-Generation** | ✅ Instant | ❌ None | ❌ 15-30 min |
| **Graduation System** | ✅ Automatic | ❌ None | ❌ Manual |
| **Web UI** | ✅ Full dashboard | ❌ CLI only | ❌ None |
| **V2 Analysis** | ✅ Session + LSP + Patterns | ❌ None | ❌ None |

**ROI**: Save ~25 hours per 100 skills vs manual creation

## 🎬 Screenshots

### Web UI Dashboard
![Dashboard](assets/screenshots/dashboard.png)

### Skill Browser
![Skill Browser](assets/screenshots/skill-browser.png)

### Graduation Candidates
![Graduation](assets/screenshots/graduation.png)

## 🌟 Why Choose Claude Auto-Skill?

!!! success "Most Comprehensive"
    The only skill system with local pattern detection, Mental Model integration, confidence evolution, and automatic graduation.

!!! tip "Time Savings"
    Save 25+ hours per 100 skills compared to manual creation. Patterns detected automatically from your actual work.

!!! info "Production Ready"
    Battle-tested with comprehensive tests, migrations system, and professional packaging. Ready for PyPI.

!!! quote "Community Powered"
    Access 27,471+ skills from skills.sh while building your own personalized skill library.

## 📚 Documentation

<div class="grid cards" markdown>

-   :material-rocket: [**Getting Started**](getting-started/installation.md)

    Installation, quick start, and configuration guide

-   :material-feature-search: [**Features**](features/overview.md)

    Deep dive into all features and capabilities

-   :material-book-open: [**User Guide**](guide/cli-commands.md)

    CLI commands, workflows, and best practices

-   :material-code-json: [**API Reference**](reference/api.md)

    Complete API documentation and architecture

</div>

## 🤝 Contributing

We welcome contributions! Check out our [Contributing Guide](contributing.md) to get started.

## 📄 License

Claude Auto-Skill is licensed under the [MIT License](https://github.com/MaTriXy/claude-auto-skill/blob/main/LICENSE).

---

<div align="center">

Made with :material-heart: by [MaTriXy](https://github.com/MaTriXy)

[Star on GitHub](https://github.com/MaTriXy/claude-auto-skill){ .md-button }

</div>
