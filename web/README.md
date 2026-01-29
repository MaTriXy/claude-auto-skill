# Auto-Skill Web UI

Beautiful visual interface for managing skills, tracking adoption, and publishing.

## Quick Start

### Easiest Way (Recommended)

From the project root:

```bash
./start-web.sh        # macOS/Linux
start-web.bat         # Windows
```

### Manual Start

```bash
# From web directory
cd web

# Install dependencies
uv sync                # With uv (recommended)
# or
pip install -r requirements.txt

# Run server
uv run python app.py   # With uv
# or
python app.py          # With pip
```

## Access

Open your browser to:
- **http://localhost:8000** (default)
- Dashboard, Graduation, and Publishing tabs available

## Features

- **Dashboard Tab**: Browse all skills with search/filter, view stats
- **Graduation Tab**: Promote proven external skills to local skills
- **Publishing Tab**: Share local skills with the community

## Custom Port

If port 8000 is in use:

```bash
./start-web.sh 3000
```

Or set in `app.py`:

```python
app.run(debug=True, host='0.0.0.0', port=3000)
```

## Requirements

- Python 3.11+ (for modern type syntax)
- Flask 3.0+
- Auto-Skill core modules

## Documentation

Full documentation: https://MaTriXy.github.io/auto-skill/features/web-ui/
