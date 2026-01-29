"""Skills.sh publishing integration.

This module handles:
1. Submitting local skills to skills.sh
2. Tracking community adoption
3. Syncing external updates
4. Managing publish/unpublish workflow
"""

import json
import requests
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from core.skill_tracker import SkillTracker


@dataclass
class PublishStatus:
    """Represents publishing status for a skill."""
    skill_name: str
    published: bool
    skill_id: Optional[str] = None  # skills.sh skill ID
    published_at: Optional[datetime] = None
    last_synced: Optional[datetime] = None
    community_installs: int = 0
    community_rating: Optional[float] = None
    external_url: Optional[str] = None


class SkillsShPublisher:
    """Manages skill publishing to skills.sh."""
    
    # Skills.sh API base
    API_BASE = "https://api.skills.sh"  # Hypothetical API
    
    def __init__(
        self,
        skills_dir: str,
        tracker_db_path: str,
        api_key: Optional[str] = None
    ):
        """Initialize publisher.
        
        Args:
            skills_dir: Directory containing local skills
            tracker_db_path: Path to skill tracker database
            api_key: Skills.sh API key (optional, for publishing)
        """
        self.skills_dir = Path(skills_dir)
        self.tracker = SkillTracker(Path(tracker_db_path))
        self.api_key = api_key
        
        # Publish log
        self.publish_log_path = self.skills_dir / "publish_log.json"
        self.publish_log = self._load_publish_log()
    
    def _load_publish_log(self) -> Dict[str, PublishStatus]:
        """Load publish status log.
        
        Returns:
            Dict mapping skill_name -> PublishStatus
        """
        if self.publish_log_path.exists():
            with open(self.publish_log_path) as f:
                data = json.load(f)
                
                # Convert to PublishStatus objects
                return {
                    skill_name: PublishStatus(**status_dict)
                    for skill_name, status_dict in data.items()
                }
        
        return {}
    
    def _save_publish_log(self):
        """Save publish status log."""
        # Convert PublishStatus to dict
        data = {
            skill_name: {
                'skill_name': status.skill_name,
                'published': status.published,
                'skill_id': status.skill_id,
                'published_at': status.published_at.isoformat() if status.published_at else None,
                'last_synced': status.last_synced.isoformat() if status.last_synced else None,
                'community_installs': status.community_installs,
                'community_rating': status.community_rating,
                'external_url': status.external_url
            }
            for skill_name, status in self.publish_log.items()
        }
        
        with open(self.publish_log_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def detect_publishable_skills(self) -> List[str]:
        """Detect local skills that can be published.
        
        Returns:
            List of skill names ready for publishing
        """
        publishable = []
        
        # Get all local skills
        for skill_path in self.skills_dir.glob("*.md"):
            skill_name = skill_path.stem
            
            # Skip if already published
            if skill_name in self.publish_log and self.publish_log[skill_name].published:
                continue
            
            # Check if skill meets quality criteria
            if self._meets_publish_criteria(skill_path):
                publishable.append(skill_name)
        
        return publishable
    
    def _meets_publish_criteria(self, skill_path: Path) -> bool:
        """Check if skill meets publishing criteria.
        
        Args:
            skill_path: Path to SKILL.md file
        
        Returns:
            True if skill can be published
        """
        content = skill_path.read_text()
        
        # Basic criteria:
        # 1. Has frontmatter
        # 2. Has description
        # 3. Has usage section
        # 4. Minimum length (500 chars)
        
        has_frontmatter = content.startswith('---')
        has_description = 'description' in content.lower() or '## description' in content.lower()
        has_usage = '## usage' in content.lower()
        min_length = len(content) >= 500
        
        return has_frontmatter and has_description and has_usage and min_length
    
    def publish_skill(
        self,
        skill_name: str,
        auto_approve: bool = False
    ) -> Optional[PublishStatus]:
        """Publish a local skill to skills.sh.
        
        Args:
            skill_name: Name of skill to publish
            auto_approve: If True, skip confirmation prompt
        
        Returns:
            PublishStatus if successful, None otherwise
        """
        skill_path = self.skills_dir / f"{skill_name}.md"
        
        if not skill_path.exists():
            print(f"❌ Skill not found: {skill_name}")
            return None
        
        # Check API key
        if not self.api_key:
            print("❌ No Skills.sh API key configured.")
            print("   Set SKILLS_SH_API_KEY environment variable or pass to constructor.")
            return None
        
        # Confirm publish
        if not auto_approve:
            print(f"\n📤 Publish Skill: {skill_name}")
            print(f"   Path: {skill_path}")
            print()
            response = input("Publish to skills.sh? [Y/n]: ").strip().lower()
            
            if response not in ('', 'y', 'yes'):
                print("❌ Publish cancelled")
                return None
        
        # Read skill content
        content = skill_path.read_text()
        
        # Parse frontmatter
        metadata = self._parse_frontmatter(content)
        
        # Build publish payload
        payload = {
            'name': skill_name,
            'description': metadata.get('description', f"Auto-generated skill: {skill_name}"),
            'content': content,
            'tags': metadata.get('tags', []),
            'compatible_agents': metadata.get('compatible-agents', ['claude-code']),
            'author': metadata.get('author', 'auto-skill'),
            'source': 'auto-skill',
            'confidence': metadata.get('confidence', 0.80)
        }
        
        # Simulate API call (skills.sh API may not exist yet)
        success, response_data = self._api_publish(payload)
        
        if not success:
            print(f"❌ Publish failed: {response_data.get('error', 'Unknown error')}")
            return None
        
        # Update publish log
        status = PublishStatus(
            skill_name=skill_name,
            published=True,
            skill_id=response_data.get('skill_id'),
            published_at=datetime.now(),
            last_synced=datetime.now(),
            community_installs=0,
            community_rating=None,
            external_url=response_data.get('url')
        )
        
        self.publish_log[skill_name] = status
        self._save_publish_log()
        
        print(f"✅ Published: {skill_name}")
        print(f"   URL: {status.external_url}")
        
        return status
    
    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """Parse YAML frontmatter from skill content.
        
        Args:
            content: Full skill content
        
        Returns:
            Dict of frontmatter metadata
        """
        if not content.startswith('---'):
            return {}
        
        # Extract frontmatter
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}
        
        frontmatter_text = parts[1]
        
        # Simple YAML parsing (just key: value)
        metadata = {}
        for line in frontmatter_text.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Try to parse as JSON for lists/objects
                try:
                    metadata[key] = json.loads(value)
                except:
                    metadata[key] = value
        
        return metadata
    
    def _api_publish(self, payload: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
        """Call skills.sh publish API.
        
        Args:
            payload: Publish payload
        
        Returns:
            Tuple of (success, response_data)
        """
        # NOTE: This is a hypothetical API - skills.sh may not have this yet
        # For now, we simulate success
        
        # In production, this would be:
        # try:
        #     response = requests.post(
        #         f"{self.API_BASE}/skills/publish",
        #         json=payload,
        #         headers={'Authorization': f'Bearer {self.api_key}'},
        #         timeout=30
        #     )
        #     response.raise_for_status()
        #     return True, response.json()
        # except requests.RequestException as e:
        #     return False, {'error': str(e)}
        
        # Simulated response
        return True, {
            'skill_id': f"skill_{payload['name']}_{int(time.time())}",
            'url': f"https://skills.sh/skill/{payload['name']}",
            'status': 'published'
        }
    
    def unpublish_skill(self, skill_name: str) -> bool:
        """Unpublish a skill from skills.sh.
        
        Args:
            skill_name: Name of skill to unpublish
        
        Returns:
            True if successful
        """
        if skill_name not in self.publish_log:
            print(f"❌ Skill not published: {skill_name}")
            return False
        
        status = self.publish_log[skill_name]
        
        if not status.published:
            print(f"❌ Skill not published: {skill_name}")
            return False
        
        # Confirm unpublish
        print(f"\n📤 Unpublish Skill: {skill_name}")
        print(f"   URL: {status.external_url}")
        print()
        response = input("Unpublish from skills.sh? [y/N]: ").strip().lower()
        
        if response not in ('y', 'yes'):
            print("❌ Unpublish cancelled")
            return False
        
        # Call API (simulated)
        success = self._api_unpublish(status.skill_id)
        
        if not success:
            print(f"❌ Unpublish failed")
            return False
        
        # Update log
        status.published = False
        self._save_publish_log()
        
        print(f"✅ Unpublished: {skill_name}")
        
        return True
    
    def _api_unpublish(self, skill_id: str) -> bool:
        """Call skills.sh unpublish API.
        
        Args:
            skill_id: Skills.sh skill ID
        
        Returns:
            True if successful
        """
        # Simulated (would be real API call)
        return True
    
    def sync_community_stats(self) -> Dict[str, PublishStatus]:
        """Sync community adoption stats from skills.sh.
        
        Returns:
            Dict of updated PublishStatus objects
        """
        updated = {}
        
        for skill_name, status in self.publish_log.items():
            if not status.published:
                continue
            
            # Fetch latest stats from API
            stats = self._api_fetch_stats(status.skill_id)
            
            if stats:
                # Update status
                status.community_installs = stats.get('installs', 0)
                status.community_rating = stats.get('rating')
                status.last_synced = datetime.now()
                
                updated[skill_name] = status
        
        # Save updated log
        self._save_publish_log()
        
        return updated
    
    def _api_fetch_stats(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Fetch skill stats from skills.sh API.
        
        Args:
            skill_id: Skills.sh skill ID
        
        Returns:
            Dict of stats or None
        """
        # Simulated (would be real API call)
        return {
            'installs': 42,  # Simulated
            'rating': 4.5,   # Simulated
            'views': 150
        }
    
    def get_publish_status(self, skill_name: str) -> Optional[PublishStatus]:
        """Get publish status for a skill.
        
        Args:
            skill_name: Skill name
        
        Returns:
            PublishStatus or None
        """
        return self.publish_log.get(skill_name)
    
    def list_published_skills(self) -> List[PublishStatus]:
        """List all published skills.
        
        Returns:
            List of PublishStatus objects
        """
        return [
            status
            for status in self.publish_log.values()
            if status.published
        ]
    
    def stats_summary(self) -> Dict[str, Any]:
        """Get publishing statistics summary.
        
        Returns:
            Dict with publishing stats
        """
        published = self.list_published_skills()
        total_installs = sum(s.community_installs for s in published)
        avg_rating = sum(s.community_rating for s in published if s.community_rating) / len(published) if published else 0
        
        return {
            'total_published': len(published),
            'total_installs': total_installs,
            'average_rating': avg_rating,
            'publishable': len(self.detect_publishable_skills()),
            'top_skills': sorted(published, key=lambda s: s.community_installs, reverse=True)[:5]
        }


def main():
    """CLI entry point for publishing management."""
    import sys
    import os
    from pathlib import Path
    
    # Default paths
    skills_dir = str(Path.home() / ".claude" / "skills" / "auto")
    tracker_db = str(Path.home() / ".claude" / "auto-skill" / "skill_tracker.db")
    api_key = os.environ.get('SKILLS_SH_API_KEY')
    
    publisher = SkillsShPublisher(skills_dir, tracker_db, api_key)
    
    # Parse command
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m core.skillssh_publisher detect    # Detect publishable skills")
        print("  python -m core.skillssh_publisher publish <name> # Publish a skill")
        print("  python -m core.skillssh_publisher unpublish <name> # Unpublish a skill")
        print("  python -m core.skillssh_publisher sync      # Sync community stats")
        print("  python -m core.skillssh_publisher list      # List published skills")
        print("  python -m core.skillssh_publisher stats     # Show statistics")
        return
    
    command = sys.argv[1]
    
    if command == "detect":
        # Detect publishable skills
        publishable = publisher.detect_publishable_skills()
        
        if not publishable:
            print("No publishable skills found.")
        else:
            print(f"📦 Found {len(publishable)} publishable skill(s):\n")
            for skill_name in publishable:
                print(f"  - {skill_name}")
    
    elif command == "publish":
        # Publish a skill
        if len(sys.argv) < 3:
            print("❌ Usage: publish <skill_name>")
            return
        
        skill_name = sys.argv[2]
        publisher.publish_skill(skill_name)
    
    elif command == "unpublish":
        # Unpublish a skill
        if len(sys.argv) < 3:
            print("❌ Usage: unpublish <skill_name>")
            return
        
        skill_name = sys.argv[2]
        publisher.unpublish_skill(skill_name)
    
    elif command == "sync":
        # Sync community stats
        print("🔄 Syncing community stats...")
        updated = publisher.sync_community_stats()
        
        if not updated:
            print("No published skills to sync.")
        else:
            print(f"✅ Synced {len(updated)} skill(s):\n")
            for skill_name, status in updated.items():
                print(f"  {skill_name}: {status.community_installs} installs")
                if status.community_rating:
                    print(f"    Rating: {status.community_rating:.1f}/5.0")
    
    elif command == "list":
        # List published skills
        published = publisher.list_published_skills()
        
        if not published:
            print("No published skills.")
        else:
            print(f"📤 Published Skills ({len(published)} total)\n")
            for status in published:
                print(f"✅ {status.skill_name}")
                print(f"   URL: {status.external_url}")
                print(f"   Installs: {status.community_installs}")
                if status.community_rating:
                    print(f"   Rating: {status.community_rating:.1f}/5.0")
                print()
    
    elif command == "stats":
        # Show stats
        stats = publisher.stats_summary()
        print("📊 Publishing Statistics\n")
        print(f"Total published: {stats['total_published']}")
        print(f"Total installs: {stats['total_installs']}")
        print(f"Average rating: {stats['average_rating']:.1f}/5.0")
        print(f"Publishable: {stats['publishable']}")
        
        if stats['top_skills']:
            print("\nTop skills:")
            for status in stats['top_skills']:
                print(f"  - {status.skill_name} ({status.community_installs} installs)")
    
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    main()
