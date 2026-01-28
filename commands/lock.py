"""
Lock file subcommand - manage skill lock file and integrity verification.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.lock_file import LockFile


def lock_command(args):
    """Handle lock file subcommands."""
    if args.lock_action == "status":
        _lock_status(args)
    elif args.lock_action == "verify":
        _lock_verify(args)
    elif args.lock_action == "list":
        _lock_list(args)
    else:
        _lock_status(args)


def _lock_status(args):
    """Show lock file status."""
    lock = LockFile()
    lock.load()

    if getattr(args, "json", False):
        print(json.dumps({
            "version": lock.version,
            "skill_count": lock.skill_count,
            "path": str(lock.path),
        }, indent=2))
        return

    print(f"\n🔒 Lock File Status\n")
    print(f"  Path: {lock.path}")
    print(f"  Version: {lock.version}")
    print(f"  Skills: {lock.skill_count}")
    print()


def _lock_verify(args):
    """Verify integrity of all locked skills."""
    lock = LockFile()
    lock.load()

    skills_dir = Path.home() / ".claude" / "skills" / "auto"
    results = lock.verify_all(skills_dir)

    if getattr(args, "json", False):
        print(json.dumps({
            "total": len(results),
            "passed": sum(1 for v in results.values() if v),
            "failed": sum(1 for v in results.values() if not v),
            "results": {k: "pass" if v else "fail" for k, v in results.items()},
        }, indent=2))
        return

    print(f"\n🔍 Integrity Verification\n")
    if not results:
        print("  No locked skills to verify.")
        return

    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)

    for name, ok in results.items():
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")

    print(f"\n  {passed} passed, {failed} failed")


def _lock_list(args):
    """List all locked skills."""
    lock = LockFile()
    lock.load()
    skills = lock.list_skills()

    if getattr(args, "json", False):
        print(json.dumps({
            "count": len(skills),
            "skills": [s.to_dict() for s in skills],
        }, indent=2))
        return

    print(f"\n🔒 Locked Skills ({len(skills)})\n")
    if not skills:
        print("  No skills locked yet.")
        return

    for skill in skills:
        print(f"  📦 {skill.name}")
        print(f"     Source: {skill.source}")
        print(f"     Hash: {skill.content_hash[:16]}...")
        print(f"     Locked: {skill.locked_at}")
        print()
