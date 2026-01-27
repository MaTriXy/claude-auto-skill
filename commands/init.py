#!/usr/bin/env python3
"""
Auto-Skill Initialization Command - Set up Auto-Skill for first use.

Creates directories, config files, and provides setup guidance.

Usage:
    python -m commands.init [--force]
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


DEFAULT_CONFIG = """---
detection:
  min_occurrences: 3         # Minimum pattern repetitions
  min_sequence_length: 2     # Shortest pattern to detect
  max_sequence_length: 10    # Longest pattern to detect
  lookback_days: 7           # Analysis window
  min_confidence: 0.7        # Threshold for suggestions
  ignored_tools:             # Tools to exclude
    - AskUserQuestion

# Hybrid configuration
hybrid:
  enable_mental: true        # Enable Mental model integration
  enable_external: true      # Enable Skills.sh discovery
  auto_graduate: true        # Auto-graduate proven skills

# V2 configuration
v2:
  enable_session_analysis: true
  enable_lsp_analysis: true
  enable_pattern_detection: true
  lsp_languages:
    - python
    - javascript
    - typescript

enabled: true
---

# Auto-Skill Configuration

This file controls Auto-Skill behavior. Adjust settings above as needed.

## Pattern Detection

- **min_occurrences**: How many times a pattern must repeat to be detected
- **min_confidence**: Threshold for suggesting skills (0.0 to 1.0)
- **lookback_days**: How far back to analyze session history

## Hybrid Features

- **enable_mental**: Use Mental model for semantic understanding (requires `mental` CLI)
- **enable_external**: Search Skills.sh for community skills
- **auto_graduate**: Automatically promote proven external skills to local

## Tips

- Start with defaults and adjust based on your workflow
- Lower `min_occurrences` to detect patterns faster (but may get false positives)
- Raise `min_confidence` to only see high-confidence patterns
- Disable `enable_external` if you only want local pattern detection
"""


def create_directory(path: Path, description: str, force: bool = False):
    """Create a directory if it doesn't exist."""
    if path.exists():
        if force:
            print(f"✓ {description}: {path} (already exists)")
        else:
            print(f"⚠ {description}: {path} (already exists, skipping)")
        return False
    
    path.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created {description}: {path}")
    return True


def create_config(path: Path, content: str, force: bool = False):
    """Create a config file if it doesn't exist."""
    if path.exists() and not force:
        print(f"⚠ Config file already exists: {path} (use --force to overwrite)")
        return False
    
    path.write_text(content)
    print(f"✓ Created config file: {path}")
    return True


def check_dependencies():
    """Check for optional dependencies."""
    print("\n🔍 Checking optional dependencies:\n")
    
    dependencies = []
    
    # Check Mental CLI
    import subprocess
    try:
        result = subprocess.run(
            ["mental", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            dependencies.append(("Mental CLI", "✅ Installed", result.stdout.strip()))
        else:
            dependencies.append(("Mental CLI", "❌ Not found", "npm install -g @mentalmodel/cli"))
    except (FileNotFoundError, subprocess.TimeoutExpired):
        dependencies.append(("Mental CLI", "❌ Not found", "npm install -g @mentalmodel/cli"))
    
    # Check if we can reach Skills.sh
    try:
        import urllib.request
        with urllib.request.urlopen("https://skills.sh", timeout=5) as response:
            if response.status == 200:
                dependencies.append(("Skills.sh API", "✅ Reachable", "https://skills.sh"))
            else:
                dependencies.append(("Skills.sh API", "⚠️  Unreachable", "Check internet connection"))
    except:
        dependencies.append(("Skills.sh API", "⚠️  Unreachable", "Check internet connection"))
    
    # Print results
    for name, status, info in dependencies:
        print(f"  {name:20} {status:20} {info}")
    
    print()


def print_next_steps():
    """Print next steps after initialization."""
    print("\n" + "="*70)
    print("🎉 Auto-Skill Initialization Complete!")
    print("="*70)
    
    print("\n📚 Next Steps:\n")
    
    print("1. **Start using Claude Code**")
    print("   - Work on your project as usual")
    print("   - Auto-Skill will record your tool usage\n")
    
    print("2. **Optional: Set up Mental Model** (for semantic understanding)")
    print("   cd your-project")
    print("   mental add domain Payment --desc 'Payment processing'")
    print("   mental add capability Checkout --operates-on Payment\n")
    
    print("3. **Discover skills** (after working for a while)")
    print("   python -m commands.discover\n")
    
    print("4. **Search external skills**")
    print("   python -m commands.discover --search 'payment'\n")
    
    print("5. **Track adoption**")
    print("   python -m commands.discover --stats\n")
    
    print("📖 Documentation:")
    print("   - README.md: Full documentation")
    print("   - planning/: Implementation details")
    print("   - examples/: Working examples\n")
    
    print("🔗 Useful Links:")
    print("   - Repository: https://github.com/MaTriXy/claude-auto-skill")
    print("   - Mental Model: https://github.com/Michaelliv/mental")
    print("   - Skills.sh: https://skills.sh\n")
    
    print("Need help? Check the README or open an issue on GitHub.\n")


def init_command(args):
    """Initialize Auto-Skill directories and config."""
    print("\n" + "="*70)
    print("🦦 Claude Auto-Skill - Initialization")
    print("="*70 + "\n")
    
    # Determine base directories
    home = Path.home()
    claude_dir = home / ".claude"
    autoskill_dir = claude_dir / "auto-skill"
    skills_dir = claude_dir / "skills" / "auto"
    
    print("📁 Creating directories:\n")
    
    # Create directories
    created = []
    created.append(create_directory(claude_dir, "Claude directory", args.force))
    created.append(create_directory(autoskill_dir, "Auto-Skill data directory", args.force))
    created.append(create_directory(skills_dir, "Auto-generated skills directory", args.force))
    
    # Create config file
    config_path = claude_dir / "auto-skill.local.md"
    print("\n📝 Creating config file:\n")
    config_created = create_config(config_path, DEFAULT_CONFIG, args.force)
    
    if config_created:
        print(f"\n📖 Config file created: {config_path}")
        print("   You can edit this file to customize Auto-Skill behavior.\n")
    
    # Check dependencies
    check_dependencies()
    
    # Summary
    print("="*70)
    print("📊 Summary")
    print("="*70 + "\n")
    
    if any(created) or config_created:
        print("✅ Initialization successful!\n")
        
        print("Created:")
        if created[0]:
            print(f"   • {claude_dir}")
        if created[1]:
            print(f"   • {autoskill_dir}")
        if created[2]:
            print(f"   • {skills_dir}")
        if config_created:
            print(f"   • {config_path}")
        print()
    else:
        print("ℹ️  All directories and config already exist.\n")
        if not args.force:
            print("   Use --force to recreate config file.\n")
    
    # Next steps
    print_next_steps()


def main():
    parser = argparse.ArgumentParser(
        description="Initialize Claude Auto-Skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m commands.init              # Initialize with defaults
  python -m commands.init --force      # Recreate config file

After initialization, start using Claude Code normally.
Auto-Skill will automatically detect patterns and suggest skills.
        """
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreate config file if it exists"
    )
    
    args = parser.parse_args()
    
    try:
        init_command(args)
    except KeyboardInterrupt:
        print("\n\n⚠️  Initialization cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
