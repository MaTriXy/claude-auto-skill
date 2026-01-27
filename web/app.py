"""Web UI for Claude Auto-Skill.

Provides:
1. Skill browser (local + external)
2. Adoption dashboard (usage stats, confidence)
3. Confidence visualization (charts)
4. Graduation management
5. Publishing controls
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, jsonify, request, send_from_directory
from core.unified_suggester import UnifiedSuggester
from core.skill_tracker import SkillTracker
from core.graduation_manager import GraduationManager
from core.skillssh_publisher import SkillsShPublisher


app = Flask(__name__)

# Configuration
CONFIG = {
    'skills_dir': str(Path.home() / ".claude" / "skills" / "auto"),
    'tracker_db': str(Path.home() / ".claude" / "auto-skill" / "skill_tracker.db"),
    'event_store_db': str(Path.home() / ".claude" / "auto-skill" / "events.db"),
}

# Initialize components
suggester = UnifiedSuggester(
    project_path=Path.cwd(),
    enable_mental=True,
    enable_external=True
)

tracker = SkillTracker(Path(CONFIG['tracker_db']))

graduation_mgr = GraduationManager(
    tracker_db_path=CONFIG['tracker_db'],
    skills_output_dir=CONFIG['skills_dir']
)

publisher = SkillsShPublisher(
    skills_dir=CONFIG['skills_dir'],
    tracker_db_path=CONFIG['tracker_db']
)


# Routes

@app.route('/')
def index():
    """Home page - skill browser."""
    return render_template('index.html')


@app.route('/api/skills')
def api_skills():
    """Get all skills (local + external)."""
    try:
        # Get local skills from tracker
        local_stats = tracker.get_all_stats()
        
        skills = []
        for skill_name, stats in local_stats.items():
            skills.append({
                'name': skill_name,
                'confidence': stats.get('confidence', 0.5),
                'source': stats.get('source', 'local'),
                'usage_count': stats.get('usage_count', 0),
                'success_count': stats.get('success_count', 0),
                'success_rate': stats.get('success_count', 0) / stats.get('usage_count', 1) if stats.get('usage_count', 0) > 0 else 0,
                'first_used': stats.get('first_used'),
                'last_used': stats.get('last_used'),
                'metadata': stats.get('metadata', {})
            })
        
        # Sort by confidence (desc)
        skills.sort(key=lambda s: s['confidence'], reverse=True)
        
        return jsonify({
            'success': True,
            'count': len(skills),
            'skills': skills
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/skills/<skill_name>')
def api_skill_detail(skill_name: str):
    """Get detailed info for a skill."""
    try:
        # Get stats
        stats = tracker.get_skill_stats(skill_name)
        
        if not stats:
            return jsonify({
                'success': False,
                'error': 'Skill not found'
            }), 404
        
        # Get confidence history
        history = tracker.get_confidence_history(skill_name)
        
        # Get publish status
        publish_status = publisher.get_publish_status(skill_name)
        
        return jsonify({
            'success': True,
            'skill': {
                'name': skill_name,
                'stats': stats,
                'confidence_history': history,
                'publish_status': {
                    'published': publish_status.published if publish_status else False,
                    'url': publish_status.external_url if publish_status else None,
                    'installs': publish_status.community_installs if publish_status else 0
                } if publish_status else None
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats/dashboard')
def api_dashboard_stats():
    """Get dashboard statistics."""
    try:
        # Overall stats
        all_stats = tracker.get_all_stats()
        
        total_skills = len(all_stats)
        local_skills = sum(1 for s in all_stats.values() if s.get('source') == 'local')
        external_skills = sum(1 for s in all_stats.values() if s.get('source') == 'external')
        
        total_usage = sum(s.get('usage_count', 0) for s in all_stats.values())
        total_success = sum(s.get('success_count', 0) for s in all_stats.values())
        avg_success_rate = total_success / total_usage if total_usage > 0 else 0
        
        # Graduation stats
        grad_stats = graduation_mgr.stats_summary()
        
        # Publishing stats
        pub_stats = publisher.stats_summary()
        
        # Top skills by usage
        top_skills = sorted(
            [
                {
                    'name': name,
                    'usage': stats.get('usage_count', 0),
                    'confidence': stats.get('confidence', 0.5)
                }
                for name, stats in all_stats.items()
            ],
            key=lambda s: s['usage'],
            reverse=True
        )[:10]
        
        return jsonify({
            'success': True,
            'stats': {
                'overview': {
                    'total_skills': total_skills,
                    'local_skills': local_skills,
                    'external_skills': external_skills,
                    'total_usage': total_usage,
                    'avg_success_rate': avg_success_rate
                },
                'graduation': grad_stats,
                'publishing': pub_stats,
                'top_skills': top_skills
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/graduation/candidates')
def api_graduation_candidates():
    """Get graduation candidates."""
    try:
        candidates = graduation_mgr.detect_candidates()
        
        return jsonify({
            'success': True,
            'count': len(candidates),
            'candidates': [
                {
                    'name': c.skill_name,
                    'confidence': c.current_confidence,
                    'usage_count': c.usage_count,
                    'success_rate': c.success_rate,
                    'source': c.source,
                    'first_used': c.first_used.isoformat() if c.first_used else None,
                    'last_used': c.last_used.isoformat() if c.last_used else None
                }
                for c in candidates
            ]
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/graduation/graduate', methods=['POST'])
def api_graduate_skill():
    """Graduate a skill."""
    try:
        data = request.get_json()
        skill_name = data.get('skill_name')
        
        if not skill_name:
            return jsonify({
                'success': False,
                'error': 'skill_name required'
            }), 400
        
        # Find candidate
        candidates = graduation_mgr.detect_candidates()
        candidate = next((c for c in candidates if c.skill_name == skill_name), None)
        
        if not candidate:
            return jsonify({
                'success': False,
                'error': 'Skill not eligible for graduation'
            }), 400
        
        # Graduate
        skill_path = graduation_mgr.graduate_skill(candidate, auto_approve=True)
        
        if not skill_path:
            return jsonify({
                'success': False,
                'error': 'Graduation failed'
            }), 500
        
        return jsonify({
            'success': True,
            'skill_path': str(skill_path)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/publish/detect')
def api_publishable_skills():
    """Get publishable skills."""
    try:
        publishable = publisher.detect_publishable_skills()
        
        return jsonify({
            'success': True,
            'count': len(publishable),
            'skills': publishable
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/publish/publish', methods=['POST'])
def api_publish_skill():
    """Publish a skill."""
    try:
        data = request.get_json()
        skill_name = data.get('skill_name')
        
        if not skill_name:
            return jsonify({
                'success': False,
                'error': 'skill_name required'
            }), 400
        
        # Publish
        status = publisher.publish_skill(skill_name, auto_approve=True)
        
        if not status:
            return jsonify({
                'success': False,
                'error': 'Publish failed'
            }), 500
        
        return jsonify({
            'success': True,
            'url': status.external_url
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/search')
def api_search():
    """Search skills."""
    try:
        query = request.args.get('q', '')
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query required'
            }), 400
        
        # Search local
        local_skills = tracker.get_all_stats()
        local_matches = [
            name for name in local_skills.keys()
            if query.lower() in name.lower()
        ]
        
        # Search external (skills.sh)
        from core.skillssh_client import SkillsShClient
        client = SkillsShClient()
        external_results = client.search(query, limit=10)
        
        return jsonify({
            'success': True,
            'query': query,
            'local_matches': local_matches,
            'external_results': external_results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory('static', filename)


if __name__ == '__main__':
    print("🦦 Claude Auto-Skill Web UI")
    print(f"   Skills directory: {CONFIG['skills_dir']}")
    print(f"   Tracker database: {CONFIG['tracker_db']}")
    print()
    print("Starting server on http://localhost:5000")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
