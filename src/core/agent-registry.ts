/**
 * Agent Registry - Tracks compatible AI coding agents and their skill directories.
 *
 * Detects installed agents, maps their skill directories, and enables
 * multi-agent skill output via symlinks.
 *
 * Ported from Python core/agent_registry.py (~267 lines).
 */

import fs from "node:fs";
import path from "node:path";
import os from "node:os";

import type { AgentConfig } from "../types";

// ---------------------------------------------------------------------------
// Well-known agent configurations
// ---------------------------------------------------------------------------

const HOME = os.homedir();

/** The 10 known AI coding agents supported by Auto-Skill. */
const KNOWN_AGENTS: AgentConfig[] = [
  {
    id: "claude-code",
    name: "Claude Code",
    skillDir: path.join(HOME, ".claude", "skills"),
    envVar: "CLAUDE_SESSION_ID",
    configFile: "~/.claude/settings.json",
    description: "Anthropic's CLI for Claude",
  },
  {
    id: "opencode",
    name: "OpenCode",
    skillDir: path.join(HOME, ".opencode", "skills"),
    configFile: "~/.opencode/config.json",
    description: "Open-source coding agent",
  },
  {
    id: "codex",
    name: "Codex CLI",
    skillDir: path.join(HOME, ".codex", "skills"),
    configFile: "~/.codex/config.yaml",
    description: "OpenAI's Codex CLI agent",
  },
  {
    id: "continue",
    name: "Continue",
    skillDir: path.join(HOME, ".continue", "skills"),
    configFile: "~/.continue/config.json",
    description: "Continue.dev IDE extension",
  },
  {
    id: "aider",
    name: "Aider",
    skillDir: path.join(HOME, ".aider", "skills"),
    configFile: "~/.aider.conf.yml",
    description: "AI pair programming tool",
  },
  {
    id: "cursor",
    name: "Cursor",
    skillDir: path.join(HOME, ".cursor", "skills"),
    configFile: "~/.cursor/settings.json",
    description: "AI-first code editor",
  },
  {
    id: "windsurf",
    name: "Windsurf",
    skillDir: path.join(HOME, ".windsurf", "skills"),
    configFile: "~/.windsurf/settings.json",
    description: "Codeium's AI IDE",
  },
  {
    id: "cline",
    name: "Cline",
    skillDir: path.join(HOME, ".cline", "skills"),
    configFile: "~/.cline/config.json",
    description: "AI coding agent for VS Code",
  },
  {
    id: "amp",
    name: "Amp",
    skillDir: path.join(HOME, ".amp", "skills"),
    configFile: "~/.amp/config.json",
    description: "Sourcegraph's AI coding agent",
  },
  {
    id: "copilot",
    name: "GitHub Copilot",
    skillDir: path.join(HOME, ".copilot", "skills"),
    configFile: "~/.config/github-copilot/hosts.json",
    description: "GitHub's AI coding assistant",
  },
];

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/**
 * Expand a tilde-prefixed path to an absolute path.
 *
 * @param filePath - A path that may start with `~/`.
 * @returns The expanded absolute path.
 */
function expandHome(filePath: string): string {
  if (filePath.startsWith("~/") || filePath === "~") {
    return path.join(HOME, filePath.slice(2));
  }
  return filePath;
}

/**
 * Check if a given agent appears to be installed on this system.
 *
 * Detection strategy (in order):
 * 1. Environment variable is set (indicates the agent is running).
 * 2. Configuration file exists on disk.
 * 3. Skill directory exists on disk.
 *
 * @param agent - The agent configuration to check.
 * @returns True if the agent appears installed, false otherwise.
 */
function isInstalled(agent: AgentConfig): boolean {
  // Check env var
  if (agent.envVar && process.env[agent.envVar]) {
    return true;
  }

  // Check config file existence
  if (agent.configFile) {
    const expanded = expandHome(agent.configFile);
    if (fs.existsSync(expanded)) {
      return true;
    }
  }

  // Check skill directory existence
  return fs.existsSync(agent.skillDir);
}

// ---------------------------------------------------------------------------
// Public factory
// ---------------------------------------------------------------------------

/**
 * Create an agent registry instance.
 *
 * Provides lookup, detection, registration, and symlink management
 * for the 10 supported AI coding agents.
 *
 * @param agents - Optional custom list of agent configs. Defaults to KNOWN_AGENTS.
 * @returns An object with agent lookup, detection, registration, and symlink methods.
 */
export function createAgentRegistry(agents?: AgentConfig[]): {
  getAgent(agentId: string): AgentConfig | null;
  listAgents(): AgentConfig[];
  detectInstalledAgents(): AgentConfig[];
  getAgentSkillDir(agentId: string): string | null;
  detectCurrentAgent(): AgentConfig | null;
  registerAgent(agent: AgentConfig): void;
  unregisterAgent(agentId: string): boolean;
  createSkillSymlinks(
    skillPath: string,
    skillName: string,
    excludeAgentId?: string,
  ): string[];
  removeSkillSymlinks(skillName: string): number;
} {
  /** Internal map from agent ID to config. */
  const agentMap = new Map<string, AgentConfig>();

  for (const a of agents ?? KNOWN_AGENTS) {
    agentMap.set(a.id, a);
  }

  // ---------------------------------------------------------------
  // getAgent
  // ---------------------------------------------------------------

  /**
   * Get an agent configuration by its ID.
   *
   * @param agentId - The agent identifier (e.g. "claude-code").
   * @returns The agent config, or null if not found.
   */
  function getAgent(agentId: string): AgentConfig | null {
    return agentMap.get(agentId) ?? null;
  }

  // ---------------------------------------------------------------
  // listAgents
  // ---------------------------------------------------------------

  /**
   * List all known agent configurations.
   *
   * @returns Array of all registered agent configs.
   */
  function listAgents(): AgentConfig[] {
    return Array.from(agentMap.values());
  }

  // ---------------------------------------------------------------
  // detectInstalledAgents
  // ---------------------------------------------------------------

  /**
   * Detect which agents are currently installed on this system.
   *
   * @returns Array of agent configs for installed agents.
   */
  function detectInstalledAgents(): AgentConfig[] {
    return Array.from(agentMap.values()).filter(isInstalled);
  }

  // ---------------------------------------------------------------
  // getAgentSkillDir
  // ---------------------------------------------------------------

  /**
   * Get the skill directory path for a specific agent.
   *
   * @param agentId - The agent identifier.
   * @returns Absolute path to the agent's skill directory, or null if unknown.
   */
  function getAgentSkillDir(agentId: string): string | null {
    const agent = agentMap.get(agentId);
    return agent ? agent.skillDir : null;
  }

  // ---------------------------------------------------------------
  // detectCurrentAgent
  // ---------------------------------------------------------------

  /**
   * Detect which agent is currently running based on environment variables.
   *
   * @returns The config for the currently running agent, or null if undetectable.
   */
  function detectCurrentAgent(): AgentConfig | null {
    for (const agent of agentMap.values()) {
      if (agent.envVar && process.env[agent.envVar]) {
        return agent;
      }
    }
    return null;
  }

  // ---------------------------------------------------------------
  // registerAgent
  // ---------------------------------------------------------------

  /**
   * Register a new agent configuration.
   *
   * If an agent with the same ID already exists, it is replaced.
   *
   * @param agent - The agent configuration to register.
   */
  function registerAgent(agent: AgentConfig): void {
    agentMap.set(agent.id, agent);
  }

  // ---------------------------------------------------------------
  // unregisterAgent
  // ---------------------------------------------------------------

  /**
   * Remove an agent from the registry.
   *
   * @param agentId - The agent identifier to remove.
   * @returns True if the agent was removed, false if it was not found.
   */
  function unregisterAgent(agentId: string): boolean {
    return agentMap.delete(agentId);
  }

  // ---------------------------------------------------------------
  // createSkillSymlinks
  // ---------------------------------------------------------------

  /**
   * Create symlinks to a skill in all installed agents' skill directories.
   *
   * Links the skill directory (or its parent when given a file path)
   * into each installed agent's skill directory, enabling cross-agent
   * skill sharing.
   *
   * @param skillPath - The canonical skill file or directory to link to.
   * @param skillName - The skill name (used as the symlink directory name).
   * @param excludeAgentId - Agent to exclude (typically the source agent).
   * @returns Array of created symlink paths.
   */
  function createSkillSymlinks(
    skillPath: string,
    skillName: string,
    excludeAgentId?: string,
  ): string[] {
    const created: string[] = [];

    // Determine the source directory to link to
    const stat = fs.existsSync(skillPath) ? fs.statSync(skillPath) : null;
    const source = stat?.isDirectory() ? skillPath : path.dirname(skillPath);

    if (!fs.existsSync(source)) {
      return created;
    }

    for (const agent of detectInstalledAgents()) {
      if (agent.id === excludeAgentId) {
        continue;
      }

      const targetDir = path.join(agent.skillDir, skillName);

      // Skip if already exists
      if (fs.existsSync(targetDir)) {
        continue;
      }

      try {
        fs.mkdirSync(path.dirname(targetDir), { recursive: true });
        fs.symlinkSync(source, targetDir, "dir");
        created.push(targetDir);
      } catch {
        // Best-effort: log and continue
      }
    }

    return created;
  }

  // ---------------------------------------------------------------
  // removeSkillSymlinks
  // ---------------------------------------------------------------

  /**
   * Remove symlinks for a skill from all agent directories.
   *
   * Only removes entries that are actual symlinks to avoid
   * accidentally deleting real directories.
   *
   * @param skillName - The skill name to remove symlinks for.
   * @returns Number of symlinks successfully removed.
   */
  function removeSkillSymlinks(skillName: string): number {
    let removed = 0;

    for (const agent of agentMap.values()) {
      const linkPath = path.join(agent.skillDir, skillName);

      try {
        const lstat = fs.lstatSync(linkPath);
        if (lstat.isSymbolicLink()) {
          fs.unlinkSync(linkPath);
          removed += 1;
        }
      } catch {
        // Path does not exist or cannot be accessed — skip
      }
    }

    return removed;
  }

  return {
    getAgent,
    listAgents,
    detectInstalledAgents,
    getAgentSkillDir,
    detectCurrentAgent,
    registerAgent,
    unregisterAgent,
    createSkillSymlinks,
    removeSkillSymlinks,
  };
}
