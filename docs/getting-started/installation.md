# Installation

Get started with Claude Auto-Skill in minutes.

## Prerequisites

Before installing, ensure you have:

- **Python 3.9+** ([Download](https://python.org))
- **uv** (recommended) or **pip** (included with Python)
- **Git** ([Download](https://git-scm.com))

Optional:

- **Node.js 16+** (for Mental CLI integration)
- **Mental CLI** (`npm install -g @mental-model/cli`)

### Installing uv (Recommended)

uv is a fast Python package installer and resolver, written in Rust:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

---

## Installation Options

=== "With uv (Recommended)"

    ```bash
    # Clone repository
    git clone https://github.com/MaTriXy/claude-auto-skill.git
    cd claude-auto-skill

    # Install dependencies (uv handles venv automatically)
    uv sync

    # Initialize
    python -m commands.init
    ```

    ✅ **Advantages**: Fastest installation, automatic venv, better dependency resolution

=== "From Source (pip)"

    ```bash
    # Clone repository
    git clone https://github.com/MaTriXy/claude-auto-skill.git
    cd claude-auto-skill

    # Install dependencies
    pip install -r requirements.txt

    # Initialize
    python -m commands.init
    ```

    ✅ **Advantages**: Latest features, easy updates, full source access

=== "PyPI (Coming Soon)"

    ```bash
    # Install via pip
    pip install claude-auto-skill

    # Initialize
    auto-skill init
    ```

    ✅ **Advantages**: One command, automatic dependencies, global CLI

=== "Development Mode"

    ```bash
    # Clone repository
    git clone https://github.com/MaTriXy/claude-auto-skill.git
    cd claude-auto-skill

    # Install in editable mode
    pip install -e .

    # Install V2 features
    pip install -r requirements-v2.txt

    # Install dev dependencies
    pip install -r requirements-dev.txt
    ```

    ✅ **Advantages**: Editable install, all features, development tools

---

## Core Installation

### 1. Clone Repository

```bash
git clone https://github.com/MaTriXy/claude-auto-skill.git
cd claude-auto-skill
```

### 2. Install Dependencies

=== "With uv (Recommended)"

    ```bash
    # Core dependencies (fastest)
    uv sync

    # With V2 features
    uv sync --extra v2

    # With dev dependencies
    uv sync --extra dev

    # Everything
    uv sync --extra all
    ```

    **Benefits**:
    - ⚡ 10-100x faster than pip
    - 🔒 Automatic lock file (`uv.lock`)
    - 📦 Handles virtual environment automatically
    - 🎯 Better dependency resolution

=== "With pip"

    ```bash
    # Core only
    pip install -r requirements.txt

    # With V2 features
    pip install -r requirements.txt -r requirements-v2.txt

    # Full (dev mode)
    pip install -r requirements.txt -r requirements-v2.txt -r requirements-dev.txt
    ```

    **Includes**:
    - PyYAML (configuration)
    - requests (skills.sh API)
    - Optional: V2 analysis, dev tools

### 3. Initialize

```bash
python -m commands.init
```

This creates:

```
~/.claude/
├── auto-skill/
│   ├── events.db           # Event store
│   ├── skill_tracker.db    # Adoption tracking
│   └── auto-skill.local.md # Configuration
└── skills/
    └── auto/               # Generated skills
```

---

## Optional: Mental CLI

For Mental Model integration:

### Install Mental

```bash
npm install -g @mental-model/cli
```

### Verify Installation

```bash
mental --version
# Output: mental 1.0.0
```

### Initialize in Project

```bash
cd your-project
mental init

# Add domains
mental add domain "Payment" --desc "Payment processing"
mental add capability "Checkout" --desc "Order checkout"
```

Auto-Skill will automatically detect and use Mental!

---

## Optional: Web UI

For the visual interface:

### Install Dependencies

=== "With uv (Recommended)"

    ```bash
    cd web
    uv sync
    ```

    ⚡ **Benefits**: Faster installation, automatic venv

=== "With pip"

    ```bash
    cd web
    pip install -r requirements.txt
    ```

### Start Server

```bash
python app.py
```

### Open Browser

Navigate to: [http://localhost:5000](http://localhost:5000)

---

## Verify Installation

Run the following commands to verify:

```bash
# Check core installation
python -c "from core import event_store; print('✅ Core installed')"

# Check V2 features (if installed)
python -c "from core import session_analyzer; print('✅ V2 installed')"

# Check configuration
ls ~/.claude/auto-skill/
# Should show: events.db, skill_tracker.db, auto-skill.local.md

# Check Mental (if installed)
mental --version
# Should show version number
```

Expected output:

```
✅ Core installed
✅ V2 installed
events.db  skill_tracker.db  auto-skill.local.md
mental 1.0.0
```

---

## Troubleshooting

### "uv: command not found"

Install uv:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

Verify installation:

```bash
uv --version
# Should show: uv 0.x.x
```

### "pip: command not found"

Install pip:

```bash
# macOS/Linux
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py

# Windows
python -m ensurepip --upgrade
```

### "Python version too old"

Upgrade Python:

```bash
# macOS (Homebrew)
brew install python@3.11

# Ubuntu/Debian
sudo apt update
sudo apt install python3.11

# Windows
# Download from python.org
```

### "Module not found"

Reinstall dependencies:

```bash
pip install --upgrade -r requirements.txt
```

### "Permission denied"

Use user install:

```bash
pip install --user -r requirements.txt
```

Or use virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### "Mental not found"

Install Node.js first:

```bash
# macOS (Homebrew)
brew install node

# Ubuntu/Debian
sudo apt install nodejs npm

# Windows
# Download from nodejs.org
```

Then install Mental:

```bash
npm install -g @mental-model/cli
```

---

## Upgrading

### From Source (with uv)

```bash
cd claude-auto-skill
git pull origin main
uv sync --upgrade
```

### From Source (with pip)

```bash
cd claude-auto-skill
git pull origin main
pip install --upgrade -r requirements.txt
```

### From PyPI (When Available)

```bash
pip install --upgrade claude-auto-skill
```

### Database Migrations

Migrations run automatically:

```python
from core.migrations import create_event_store_migrations

manager = create_event_store_migrations()
manager.migrate()  # Apply pending migrations
```

---

## Uninstallation

### Remove Installation

```bash
# Remove repository
rm -rf claude-auto-skill

# Remove data (WARNING: deletes all skills and history)
rm -rf ~/.claude/auto-skill
rm -rf ~/.claude/skills/auto
```

### Keep Data, Remove Code

```bash
# Only remove repository
rm -rf claude-auto-skill

# Data remains in ~/.claude/
```

---

## Platform-Specific Notes

### macOS

- ✅ Native support
- ✅ All features work
- Install via Homebrew recommended:
  ```bash
  brew install python git node
  ```

### Linux

- ✅ Native support
- ✅ All features work
- Use system package manager:
  ```bash
  sudo apt install python3 python3-pip git nodejs npm
  ```

### Windows

- ✅ Supported
- ⚠️ Path differences (use `\` instead of `/`)
- ⚠️ PowerShell recommended over CMD
- Install via official installers

**Windows-specific paths**:

```powershell
# Data directory
%USERPROFILE%\.claude\auto-skill

# Configuration
%USERPROFILE%\.claude\auto-skill\auto-skill.local.md
```

---

## Docker (Optional)

Run in container:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-m", "commands.discover"]
```

Build and run:

```bash
docker build -t auto-skill .
docker run -v ~/.claude:/root/.claude auto-skill
```

---

## Next Steps

<div class="grid cards" markdown>

-   :material-rocket: **[Quick Start](quick-start.md)**

    Generate your first skill in 5 minutes

-   :material-cog: **[Configuration](configuration.md)**

    Customize detection and behavior

-   :material-book: **[User Guide](../guide/cli-commands.md)**

    Complete command reference

</div>
