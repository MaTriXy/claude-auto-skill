#!/usr/bin/env python3
"""
Verify Claude Auto-Skill V2 installation.

This script checks that all V2 modules are properly installed and importable.
"""

import sys
from pathlib import Path

def verify_installation():
    """Verify all core modules can be imported."""
    print("=" * 60)
    print("CLAUDE AUTO-SKILL V2 - INSTALLATION VERIFICATION")
    print("=" * 60)
    print()
    
    # Check location
    current_path = Path(__file__).parent.resolve()
    print(f"📍 Location: {current_path}")
    print()
    
    # Check core modules
    print("Checking core modules...")
    modules_to_check = [
        ("core.event_store", "EventStore"),
        ("core.sequence_matcher", "SequenceMatcher"),
        ("core.config", "Config"),
        ("core.session_analyzer", "SessionAnalyzer"),
        ("core.lsp_analyzer", "LSPAnalyzer"),
        ("core.design_pattern_detector", "DesignPatternDetector"),
        ("core.pattern_detector", "PatternDetector"),
        ("core.skill_generator", "SkillGenerator"),
    ]
    
    all_passed = True
    for module_name, class_name in modules_to_check:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"  ✅ {module_name}.{class_name}")
        except ImportError as e:
            print(f"  ❌ {module_name}.{class_name} - Import Error: {e}")
            all_passed = False
        except AttributeError as e:
            print(f"  ❌ {module_name}.{class_name} - Not Found: {e}")
            all_passed = False
        except Exception as e:
            print(f"  ❌ {module_name}.{class_name} - Error: {e}")
            all_passed = False
    
    print()
    
    # Check files
    print("Checking required files...")
    required_files = [
        "README.md",
        "requirements.txt",
        "core/__init__.py",
        "core/event_store.py",
        "core/session_analyzer.py",
        "core/lsp_analyzer.py",
        "core/design_pattern_detector.py",
        "core/pattern_detector.py",
        "core/skill_generator.py",
        "tests/test_v2_integration.py",
    ]
    
    for file_path in required_files:
        full_path = current_path / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - NOT FOUND")
            all_passed = False
    
    print()
    print("=" * 60)
    
    if all_passed:
        print("✅ INSTALLATION VERIFIED - All modules ready!")
        print()
        print("Next steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Run tests: pytest tests/test_v2_integration.py -v")
        print("  3. Start using V2 features!")
        return 0
    else:
        print("❌ INSTALLATION INCOMPLETE - Some modules missing")
        return 1

if __name__ == "__main__":
    sys.exit(verify_installation())
