#!/bin/bash
# Start Auto-Skill Web UI

echo "🦦 Auto-Skill Web UI"
echo "================================"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Get the port (default 8000, or from first argument)
PORT="${1:-8000}"

echo "📦 Installing dependencies..."
uv pip install -r requirements.txt > /dev/null 2>&1

echo "✅ Dependencies ready"
echo ""
echo "🚀 Starting server on http://localhost:$PORT"
echo "   Press Ctrl+C to stop"
echo ""

# Run the Flask app
cd "$(dirname "$0")"
uv run python -c "
from pathlib import Path
import sys
sys.path.insert(0, str(Path('.').parent))
from app import app

print('📊 Dashboard: http://localhost:$PORT')
print('⭐ Graduation: http://localhost:$PORT#graduation')
print('📤 Publishing: http://localhost:$PORT#publishing')
print()

app.run(debug=True, host='0.0.0.0', port=$PORT)
"
