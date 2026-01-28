"""
Agent management subcommand - list, detect, and manage agent configurations.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent_registry import AgentRegistry


def agents_command(args):
    """Handle agent-related subcommands."""
    registry = AgentRegistry()

    if args.agent_action == "list":
        _list_agents(registry, args)
    elif args.agent_action == "detect":
        _detect_agents(registry, args)
    else:
        _list_agents(registry, args)


def _list_agents(registry: AgentRegistry, args):
    """List all known agents."""
    agents = registry.list_agents()

    if getattr(args, "json", False):
        print(json.dumps({
            "count": len(agents),
            "agents": [
                {
                    "id": a.id,
                    "name": a.name,
                    "skill_dir": str(a.skill_dir),
                    "installed": a.is_installed,
                    "description": a.description,
                }
                for a in agents
            ],
        }, indent=2))
        return

    print(f"\n🤖 Known Agents ({len(agents)} total)\n")
    for agent in agents:
        status = "✅" if agent.is_installed else "❌"
        print(f"  {status} {agent.name} ({agent.id})")
        print(f"     Skills: {agent.skill_dir}")
        if agent.description:
            print(f"     {agent.description}")
        print()


def _detect_agents(registry: AgentRegistry, args):
    """Detect installed agents."""
    installed = registry.detect_installed_agents()

    if getattr(args, "json", False):
        print(json.dumps({
            "count": len(installed),
            "agents": [
                {"id": a.id, "name": a.name, "skill_dir": str(a.skill_dir)}
                for a in installed
            ],
        }, indent=2))
        return

    print(f"\n🔍 Detected Agents ({len(installed)} installed)\n")
    if not installed:
        print("  No agents detected. Install an agent to get started.")
        return

    for agent in installed:
        print(f"  ✅ {agent.name} ({agent.id})")
        print(f"     Skills: {agent.skill_dir}")
        print()
