#!/usr/bin/env bash
# Auto-Skill CLI Installation Script
# This script is automatically triggered after 'npx skills add MaTriXy/auto-skill'

set -e

echo "🔧 Auto-Skill CLI Installation"
echo ""

# Check if we're in a CI environment
if [ -n "$CI" ]; then
    echo "⚠️  CI environment detected. Skipping CLI installation."
    exit 0
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "⚠️  Python 3 not found. CLI installation skipped."
    echo "   Install Python 3.9+ to use auto-skill CLI commands."
    exit 0
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Python $PYTHON_VERSION found"
echo ""

# Check for pip/uv
HAS_UV=false
HAS_PIP=false

if command -v uv &> /dev/null; then
    HAS_UV=true
    echo "✓ uv found (recommended)"
elif command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
    HAS_PIP=true
    echo "✓ pip found"
else
    echo "⚠️  No package manager found (pip or uv)."
    echo "   Install pip or uv to use auto-skill CLI commands."
    exit 0
fi

echo ""
echo "The auto-skill CLI tool provides commands like:"
echo "  • auto-skill init"
echo "  • auto-skill discover"
echo "  • auto-skill search"
echo "  • auto-skill stats"
echo ""

# Non-interactive check - look for --yes flag or AUTO_SKILL_AUTO_INSTALL env var
AUTO_INSTALL=${AUTO_SKILL_AUTO_INSTALL:-false}

if [ "$AUTO_INSTALL" = "true" ]; then
    INSTALL="y"
else
    read -p "Would you like to install the CLI tool now? (y/N) " -n 1 -r INSTALL
    echo ""
fi

if [[ $INSTALL =~ ^[Yy]$ ]]; then
    echo ""
    echo "Installing auto-skill CLI..."
    
    REPO_URL="git+https://github.com/MaTriXy/auto-skill.git"
    
    if [ "$HAS_UV" = true ]; then
        # Check if we're in a venv
        if [ -z "$VIRTUAL_ENV" ]; then
            echo "⚠️  Not in a virtual environment."
            read -p "Install globally with uv? (y/N) " -n 1 -r GLOBAL
            echo ""
            if [[ $GLOBAL =~ ^[Yy]$ ]]; then
                uvx --from "$REPO_URL" auto-skill version || uv tool install "$REPO_URL"
                echo ""
                echo "✅ Installed! Run: uvx auto-skill init"
            else
                echo "💡 Create a venv first: uv venv && source .venv/bin/activate"
                echo "   Then run: uv pip install $REPO_URL"
            fi
        else
            uv pip install "$REPO_URL"
            echo ""
            echo "✅ Installed! Run: auto-skill init"
        fi
    else
        # Using pip
        if [ -z "$VIRTUAL_ENV" ]; then
            echo "⚠️  Not in a virtual environment."
            read -p "Install globally with pip? (requires sudo) (y/N) " -n 1 -r GLOBAL
            echo ""
            if [[ $GLOBAL =~ ^[Yy]$ ]]; then
                pip3 install --user "$REPO_URL"
                echo ""
                echo "✅ Installed! You may need to add ~/.local/bin to PATH"
                echo "   Then run: auto-skill init"
            else
                echo "💡 Create a venv first: python3 -m venv .venv && source .venv/bin/activate"
                echo "   Then run: pip install $REPO_URL"
            fi
        else
            pip3 install "$REPO_URL"
            echo ""
            echo "✅ Installed! Run: auto-skill init"
        fi
    fi
else
    echo ""
    echo "⏭️  Skipped CLI installation."
    echo ""
    echo "To install later, run:"
    if [ "$HAS_UV" = true ]; then
        echo "  uv pip install git+https://github.com/MaTriXy/auto-skill.git"
    else
        echo "  pip install git+https://github.com/MaTriXy/auto-skill.git"
    fi
    echo ""
    echo "Or set AUTO_SKILL_AUTO_INSTALL=true to auto-install next time."
fi

echo ""
echo "📚 Agent skills installed successfully!"
echo "   Skills available in: .agents/skills/"
