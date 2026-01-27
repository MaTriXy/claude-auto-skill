"""Automatic skill graduation from external to local.

This module handles:
1. Detection of graduation candidates (external skills with high confidence)
2. User approval workflow
3. Generation of local skills from external sources
4. Metadata updates and tracking
"""

import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from core.skill_tracker import SkillTracker
from core.skill_generator import SkillGenerator
from core.pattern_detector import DetectedPattern


@dataclass
class GraduationCandidate:
    """Represents a skill eligible for graduation."""
    skill_name: str
    current_confidence: float
    usage_count: int
    success_count: int
    success_rate: float
    first_used: datetime
    last_used: datetime
    source: str  # "external" or "mental-hint"
    metadata: Optional[Dict[str, Any]] = None
    
    def meets_criteria(self) -> bool:
        """Check if skill meets graduation criteria."""
        return (
            self.current_confidence >= 0.85 and
            self.usage_count >= 5 and
            self.success_rate >= 0.80
        )


class GraduationManager:
    """Manages automatic skill graduation workflow."""
    
    # Graduation thresholds
    MIN_CONFIDENCE = 0.85
    MIN_USAGE_COUNT = 5
    MIN_SUCCESS_RATE = 0.80
    
    def __init__(self, tracker_db_path: str, skills_output_dir: str):
        """Initialize graduation manager.

        Args:
            tracker_db_path: Path to skill tracker database
            skills_output_dir: Directory to save graduated skills
        """
        self.tracker = SkillTracker(Path(tracker_db_path))
        self.skills_dir = Path(skills_output_dir)
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        
        # Graduation log
        self.graduation_log_path = self.skills_dir / "graduation_log.json"
        self.graduation_log = self._load_graduation_log()
    
    def _load_graduation_log(self) -> List[Dict[str, Any]]:
        """Load graduation history."""
        if self.graduation_log_path.exists():
            with open(self.graduation_log_path) as f:
                return json.load(f)
        return []
    
    def _save_graduation_log(self):
        """Save graduation history."""
        with open(self.graduation_log_path, 'w') as f:
            json.dump(self.graduation_log, f, indent=2, default=str)
    
    def detect_candidates(self) -> List[GraduationCandidate]:
        """Detect skills eligible for graduation.
        
        Returns:
            List of graduation candidates sorted by confidence (desc)
        """
        candidates = []
        
        # Get all skills from tracker
        stats = self.tracker.get_all_stats()
        
        for skill_name, skill_stats in stats.items():
            # Skip if already graduated
            if self._is_graduated(skill_name):
                continue
            
            # Skip if local skill
            if skill_stats.get('source') == 'local':
                continue
            
            # Check if external or mental-hint
            source = skill_stats.get('source', 'external')
            if source not in ('external', 'mental-hint'):
                continue
            
            # Build candidate
            usage_count = skill_stats.get('usage_count', 0)
            success_count = skill_stats.get('success_count', 0)
            success_rate = success_count / usage_count if usage_count > 0 else 0
            
            candidate = GraduationCandidate(
                skill_name=skill_name,
                current_confidence=skill_stats.get('confidence', 0.5),
                usage_count=usage_count,
                success_count=success_count,
                success_rate=success_rate,
                first_used=skill_stats.get('first_used'),
                last_used=skill_stats.get('last_used'),
                source=source,
                metadata=skill_stats.get('metadata')
            )
            
            # Only include if meets criteria
            if candidate.meets_criteria():
                candidates.append(candidate)
        
        # Sort by confidence (desc)
        candidates.sort(key=lambda c: c.current_confidence, reverse=True)
        
        return candidates
    
    def _is_graduated(self, skill_name: str) -> bool:
        """Check if skill has already been graduated."""
        return any(
            entry['skill_name'] == skill_name
            for entry in self.graduation_log
        )
    
    def prompt_for_approval(self, candidate: GraduationCandidate) -> bool:
        """Prompt user for graduation approval.
        
        Args:
            candidate: Graduation candidate
        
        Returns:
            True if approved, False otherwise
        """
        print(f"\n🎓 Graduation Candidate: {candidate.skill_name}")
        print(f"   Confidence: {candidate.current_confidence:.0%}")
        print(f"   Usage: {candidate.usage_count} times ({candidate.success_rate:.0%} success)")
        print(f"   Source: {candidate.source}")
        
        if candidate.metadata:
            print(f"   Author: {candidate.metadata.get('author', 'Unknown')}")
            if 'tags' in candidate.metadata:
                print(f"   Tags: {', '.join(candidate.metadata['tags'][:5])}")
        
        print()
        response = input("Graduate this skill to local? [Y/n]: ").strip().lower()
        
        return response in ('', 'y', 'yes')
    
    def graduate_skill(
        self,
        candidate: GraduationCandidate,
        auto_approve: bool = False
    ) -> Optional[Path]:
        """Graduate an external skill to local.
        
        Args:
            candidate: Graduation candidate
            auto_approve: If True, skip user approval
        
        Returns:
            Path to generated skill file, or None if cancelled
        """
        # Check approval
        if not auto_approve:
            if not self.prompt_for_approval(candidate):
                print("❌ Graduation cancelled")
                return None
        
        # Generate local skill from external metadata
        skill_path = self._generate_local_skill(candidate)
        
        # Update tracker (promote to local)
        self.tracker.record_adoption(
            skill_name=candidate.skill_name,
            source='local',  # Promoted!
            success=True,
            metadata={
                **candidate.metadata,
                'graduated_from': candidate.source,
                'graduated_at': datetime.now().isoformat(),
                'original_confidence': candidate.current_confidence
            }
        )
        
        # Update confidence to local level (0.80)
        self.tracker.update_confidence(
            skill_name=candidate.skill_name,
            new_confidence=0.80
        )
        
        # Log graduation
        self.graduation_log.append({
            'skill_name': candidate.skill_name,
            'graduated_at': datetime.now().isoformat(),
            'graduated_from': candidate.source,
            'usage_count': candidate.usage_count,
            'success_rate': candidate.success_rate,
            'final_confidence': 0.80,
            'skill_path': str(skill_path)
        })
        self._save_graduation_log()
        
        print(f"✅ Graduated: {candidate.skill_name}")
        print(f"   Saved to: {skill_path}")
        print(f"   New confidence: 80% (local)")
        
        return skill_path
    
    def _generate_local_skill(self, candidate: GraduationCandidate) -> Path:
        """Generate local skill file from external candidate.
        
        Args:
            candidate: Graduation candidate with metadata
        
        Returns:
            Path to generated SKILL.md
        """
        # Create a pseudo-pattern for skill generator
        # (graduation uses external metadata, not pattern detection)
        pattern = DetectedPattern(
            name=candidate.skill_name,
            description=candidate.metadata.get('description', f"Graduated skill: {candidate.skill_name}"),
            tool_sequence=[],
            occurrences=candidate.usage_count,
            confidence=0.80,  # Local starting confidence
            mental_context=candidate.metadata.get('mental_context')
        )
        
        # Generate skill
        generator = SkillGenerator(output_dir=str(self.skills_dir))
        
        # Override metadata for graduated skill
        skill_content = self._build_graduated_skill_content(candidate)
        
        # Save skill
        skill_path = self.skills_dir / f"{candidate.skill_name}.md"
        skill_path.write_text(skill_content)
        
        return skill_path
    
    def _build_graduated_skill_content(self, candidate: GraduationCandidate) -> str:
        """Build SKILL.md content for graduated skill.
        
        Args:
            candidate: Graduation candidate
        
        Returns:
            Formatted SKILL.md content
        """
        metadata = candidate.metadata or {}
        
        # Build frontmatter
        frontmatter = f"""---
name: {candidate.skill_name}
confidence: 0.80

# Source
source: local
derived-from: {candidate.source}
graduated-at: {datetime.now().isoformat()}

# Adoption stats
usage-count: {candidate.usage_count}
success-rate: {candidate.success_rate:.2f}
first-used: {candidate.first_used.isoformat() if candidate.first_used else 'unknown'}
last-used: {candidate.last_used.isoformat() if candidate.last_used else 'unknown'}

# Vercel compatibility
compatible-agents: [claude-code, opencode, codex]
tags: {json.dumps(metadata.get('tags', []))}
"""
        
        if metadata.get('mental_context'):
            mental = metadata['mental_context']
            if mental.get('domains'):
                frontmatter += f"\n# Mental context\ndomains: {json.dumps([d['name'] for d in mental['domains']])}\n"
        
        frontmatter += "---\n\n"
        
        # Build body
        body = f"""# {candidate.skill_name}

**Graduated from**: {candidate.source}
**Status**: Local (promoted from external)

## Description

{metadata.get('description', 'No description available')}

## Why This Skill Was Graduated

This skill was automatically graduated from external ({candidate.source}) to local based on proven adoption:

- **Usage**: {candidate.usage_count} times
- **Success Rate**: {candidate.success_rate:.0%}
- **Final Confidence**: 80% (local)

The skill has been validated through real-world usage and promoted to a trusted local skill.

## Original Metadata

"""
        
        if metadata.get('author'):
            body += f"- **Original Author**: {metadata['author']}\n"
        
        if metadata.get('installs'):
            body += f"- **Community Installs**: {metadata['installs']}\n"
        
        if metadata.get('url'):
            body += f"- **Original Source**: {metadata['url']}\n"
        
        body += "\n## Usage\n\n"
        body += metadata.get('usage', 'Use this skill by referencing it in your workflow.')
        
        body += "\n\n## Success Indicators\n\n"
        body += "- Task completed successfully\n"
        body += "- No errors or warnings\n"
        body += "- Code quality maintained\n"
        
        return frontmatter + body
    
    def auto_graduate_all(self, max_count: int = 5) -> List[Path]:
        """Automatically graduate top candidates without prompting.
        
        Args:
            max_count: Maximum number of skills to graduate
        
        Returns:
            List of paths to graduated skills
        """
        candidates = self.detect_candidates()[:max_count]
        
        if not candidates:
            print("No graduation candidates found.")
            return []
        
        print(f"🎓 Auto-graduating {len(candidates)} skill(s)...\n")
        
        graduated = []
        for candidate in candidates:
            skill_path = self.graduate_skill(candidate, auto_approve=True)
            if skill_path:
                graduated.append(skill_path)
        
        return graduated
    
    def get_graduation_history(self) -> List[Dict[str, Any]]:
        """Get graduation history.
        
        Returns:
            List of graduation log entries
        """
        return self.graduation_log.copy()
    
    def stats_summary(self) -> Dict[str, Any]:
        """Get graduation statistics summary.
        
        Returns:
            Dict with graduation stats
        """
        total_graduated = len(self.graduation_log)
        candidates = self.detect_candidates()
        
        return {
            'total_graduated': total_graduated,
            'pending_candidates': len(candidates),
            'graduation_rate': f"{(total_graduated / (total_graduated + len(candidates))) * 100:.1f}%" if total_graduated + len(candidates) > 0 else "0%",
            'recent_graduations': self.graduation_log[-5:] if self.graduation_log else []
        }


def main():
    """CLI entry point for graduation management."""
    import sys
    from pathlib import Path
    
    # Default paths
    tracker_db = str(Path.home() / ".claude" / "auto-skill" / "skill_tracker.db")
    skills_dir = str(Path.home() / ".claude" / "skills" / "auto")
    
    manager = GraduationManager(tracker_db, skills_dir)
    
    # Parse command
    if len(sys.argv) < 2:
        # Default: detect and prompt
        candidates = manager.detect_candidates()
        
        if not candidates:
            print("✅ No graduation candidates found.")
            print("\nSkills are graduated when they meet:")
            print(f"  - Confidence ≥ {manager.MIN_CONFIDENCE:.0%}")
            print(f"  - Usage ≥ {manager.MIN_USAGE_COUNT}")
            print(f"  - Success rate ≥ {manager.MIN_SUCCESS_RATE:.0%}")
            return
        
        print(f"🎓 Found {len(candidates)} graduation candidate(s):\n")
        
        for i, candidate in enumerate(candidates, 1):
            print(f"{i}. {candidate.skill_name}")
            print(f"   Confidence: {candidate.current_confidence:.0%} | Usage: {candidate.usage_count} | Success: {candidate.success_rate:.0%}")
        
        print()
        
        # Prompt for each
        for candidate in candidates:
            manager.graduate_skill(candidate, auto_approve=False)
        
        return
    
    command = sys.argv[1]
    
    if command == "detect":
        # Just detect, don't prompt
        candidates = manager.detect_candidates()
        
        if not candidates:
            print("No graduation candidates found.")
        else:
            print(f"Found {len(candidates)} candidate(s):\n")
            for candidate in candidates:
                print(f"- {candidate.skill_name} ({candidate.current_confidence:.0%})")
    
    elif command == "auto":
        # Auto-graduate without prompting
        max_count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        manager.auto_graduate_all(max_count)
    
    elif command == "stats":
        # Show graduation stats
        stats = manager.stats_summary()
        print("📊 Graduation Statistics\n")
        print(f"Total graduated: {stats['total_graduated']}")
        print(f"Pending candidates: {stats['pending_candidates']}")
        print(f"Graduation rate: {stats['graduation_rate']}")
        
        if stats['recent_graduations']:
            print("\nRecent graduations:")
            for entry in stats['recent_graduations']:
                print(f"  - {entry['skill_name']} (success rate: {entry['success_rate']:.0%})")
    
    elif command == "history":
        # Show full graduation history
        history = manager.get_graduation_history()
        
        if not history:
            print("No graduation history yet.")
        else:
            print(f"📜 Graduation History ({len(history)} total)\n")
            for entry in history:
                print(f"✅ {entry['skill_name']}")
                print(f"   Graduated: {entry['graduated_at']}")
                print(f"   From: {entry['graduated_from']}")
                print(f"   Usage: {entry['usage_count']} times ({entry['success_rate']:.0%} success)")
                print()
    
    else:
        print("Usage:")
        print("  python -m core.graduation_manager         # Detect and prompt for each")
        print("  python -m core.graduation_manager detect  # Just detect candidates")
        print("  python -m core.graduation_manager auto [n] # Auto-graduate top n (default 5)")
        print("  python -m core.graduation_manager stats   # Show statistics")
        print("  python -m core.graduation_manager history # Show full history")


if __name__ == "__main__":
    main()
