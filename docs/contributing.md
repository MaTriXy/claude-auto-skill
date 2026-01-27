# Contributing to Claude Auto-Skill

Thank you for your interest in contributing! 🎉

## Ways to Contribute

- 🐛 **Bug Reports**: [Open an issue](https://github.com/MaTriXy/claude-auto-skill/issues)
- ✨ **Feature Requests**: [Start a discussion](https://github.com/MaTriXy/claude-auto-skill/discussions)
- 📝 **Documentation**: Improve docs, add examples
- 🔧 **Code**: Fix bugs, add features
- 🎨 **Design**: UI/UX improvements
- 📦 **Skills**: Share your best skills

---

## Getting Started

### 1. Fork & Clone

```bash
# Fork on GitHub first
git clone https://github.com/YOUR_USERNAME/claude-auto-skill.git
cd claude-auto-skill
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-v2.txt
pip install -r requirements-dev.txt

# Initialize
python -m commands.init
```

### 3. Create Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

---

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_pattern_detector.py

# Run with coverage
pytest --cov=core --cov-report=html

# Run only fast tests
pytest -m "not slow"
```

### Code Quality

```bash
# Format code
black .

# Check style
flake8 core/ tests/

# Type checking
mypy core/
```

### Testing Locally

```bash
# Test pattern detection
python run_detector.py

# Test CLI commands
python -m commands.discover --json

# Test Web UI
cd web && python app.py
```

---

## Pull Request Process

### 1. Make Changes

- Follow existing code style
- Add tests for new features
- Update documentation
- Add docstrings (Google style)

### 2. Run Checks

```bash
# Format
black .

# Lint
flake8 core/ tests/

# Test
pytest

# Type check
mypy core/
```

### 3. Commit

```bash
git add .
git commit -m "type: description"
```

**Commit Types**:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Add tests
- `chore`: Maintenance

**Examples**:

```bash
git commit -m "feat: add skill export command"
git commit -m "fix: handle empty event store"
git commit -m "docs: improve graduation guide"
```

### 4. Push & Create PR

```bash
git push origin feature/your-feature-name
```

Then create Pull Request on GitHub.

**PR Description Template**:

```markdown
## Description
Brief description of changes

## Type
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Refactor

## Testing
- [ ] Added tests
- [ ] All tests pass
- [ ] Manual testing done

## Screenshots (if applicable)
```

---

## Code Style

### Python Style Guide

Follow [PEP 8](https://pep8.org):

```python
# Good
def detect_patterns(
    events: List[Event],
    min_occurrences: int = 3
) -> List[Pattern]:
    """Detect repeated patterns from events.
    
    Args:
        events: List of tool call events
        min_occurrences: Minimum pattern occurrences
    
    Returns:
        List of detected patterns
    """
    pass

# Bad
def detectPatterns(events,minOccurrences=3):
    pass
```

### Docstrings

Use [Google Style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings):

```python
def graduate_skill(skill_name: str, auto_approve: bool = False) -> Optional[Path]:
    """Graduate an external skill to local.
    
    Promotes a proven external skill to a trusted local skill after
    meeting graduation criteria (≥85% confidence, ≥5 uses, ≥80% success).
    
    Args:
        skill_name: Name of skill to graduate
        auto_approve: If True, skip user confirmation prompt
    
    Returns:
        Path to generated skill file, or None if cancelled
    
    Raises:
        ValueError: If skill doesn't meet graduation criteria
        FileNotFoundError: If skill file not found
    
    Example:
        >>> manager = GraduationManager(db_path, skills_dir)
        >>> path = manager.graduate_skill("stripe-integration")
        >>> print(f"Graduated to: {path}")
    """
    pass
```

### Type Hints

Always use type hints:

```python
from typing import List, Optional, Dict, Any

def process_events(
    events: List[Event],
    config: Dict[str, Any]
) -> Optional[List[Pattern]]:
    pass
```

---

## Adding Features

### New Pattern Detector

1. **Create detector** in `core/`:

```python
# core/my_detector.py
class MyDetector:
    """Detects my pattern type."""
    
    def detect(self, events: List[Event]) -> List[Pattern]:
        """Detect patterns."""
        pass
```

2. **Add tests** in `tests/`:

```python
# tests/test_my_detector.py
def test_my_detector():
    detector = MyDetector()
    patterns = detector.detect(sample_events)
    assert len(patterns) > 0
```

3. **Integrate** in pipeline:

```python
# core/unified_suggester.py
from core.my_detector import MyDetector

def suggest_for_context(self, context):
    my_patterns = MyDetector().detect(events)
    # ... combine with other sources
```

4. **Document**:

- Add to `docs/features/pattern-detection.md`
- Update `README.md`
- Add docstrings

### New CLI Command

1. **Create command** in `commands/`:

```python
# commands/my_command.py
def main():
    """My command description."""
    import sys
    # ... implementation
    
if __name__ == "__main__":
    main()
```

2. **Add entry point** in `pyproject.toml`:

```toml
[project.scripts]
auto-skill-my-command = "commands.my_command:main"
```

3. **Document** in `docs/guide/cli-commands.md`

### New Web UI Feature

1. **Add API endpoint** in `web/app.py`:

```python
@app.route('/api/my-feature')
def api_my_feature():
    return jsonify({'success': True, 'data': []})
```

2. **Add frontend** in `web/templates/index.html`:

```html
<button onclick="callMyFeature()">My Feature</button>

<script>
async function callMyFeature() {
    const response = await fetch('/api/my-feature');
    const data = await response.json();
    // ... handle data
}
</script>
```

3. **Document** in `docs/features/web-ui.md`

---

## Testing Guidelines

### Test Structure

```python
import pytest
from core.my_module import MyClass

@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {"key": "value"}

class TestMyClass:
    """Test suite for MyClass."""
    
    def test_basic_functionality(self, sample_data):
        """Test basic functionality."""
        obj = MyClass()
        result = obj.process(sample_data)
        assert result == expected
    
    def test_edge_case(self):
        """Test edge case handling."""
        obj = MyClass()
        with pytest.raises(ValueError):
            obj.process(invalid_data)
```

### Coverage Requirements

- **Core modules**: ≥80% coverage
- **CLI commands**: ≥60% coverage
- **Web UI**: Manual testing OK

---

## Documentation

### Adding Documentation

1. **Create markdown** in `docs/`:

```markdown
# My Feature

Description of feature.

## Usage

\```bash
python -m commands.my-feature
\```

## Examples

...
```

2. **Add to navigation** in `mkdocs.yml`:

```yaml
nav:
  - Features:
    - My Feature: features/my-feature.md
```

3. **Build locally**:

```bash
pip install mkdocs-material
mkdocs serve
# Open http://localhost:8000
```

### Screenshot Guidelines

See `docs/assets/SCREENSHOTS.md` for details.

---

## Release Process

*For maintainers:*

### 1. Update Version

```python
# core/__version__.py
__version__ = "2.1.0"
```

### 2. Update Changelog

```markdown
# docs/changelog.md
## [2.1.0] - 2026-01-27

### Added
- New feature X
- New feature Y

### Fixed
- Bug fix Z
```

### 3. Create Release

```bash
git tag v2.1.0
git push origin v2.1.0
```

### 4. Publish to PyPI

```bash
python -m build
python -m twine upload dist/*
```

---

## Community

### Code of Conduct

Be respectful, inclusive, and constructive.

### Getting Help

- 💬 [GitHub Discussions](https://github.com/MaTriXy/claude-auto-skill/discussions)
- 🐛 [GitHub Issues](https://github.com/MaTriXy/claude-auto-skill/issues)
- 🐦 [Twitter @MaTriXy](https://twitter.com/MaTriXy)

### Recognition

Contributors are recognized in:

- `CONTRIBUTORS.md`
- GitHub Contributors page
- Release notes

---

## Questions?

Don't hesitate to ask! Open a [discussion](https://github.com/MaTriXy/claude-auto-skill/discussions) or [issue](https://github.com/MaTriXy/claude-auto-skill/issues).

**Thank you for contributing!** 🦦✨
