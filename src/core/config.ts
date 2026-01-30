/**
 * Configuration management for Auto-Skill.
 *
 * Handles default settings and project-specific overrides.
 */

import path from "node:path";
import fs from "node:fs";

import yaml from "yaml";

import type {
  DetectionConfig,
  AgentSettings,
  ProviderSettings,
  Config,
} from "../types";

/** Path to project-local config overrides. */
const LOCAL_CONFIG_FILE = ".claude/auto-skill.local.md";

/** Default detection configuration. */
function defaultDetectionConfig(): DetectionConfig {
  return {
    minOccurrences: 3,
    minSequenceLength: 2,
    maxSequenceLength: 10,
    lookbackDays: 7,
    minConfidence: 0.7,
    ignoredTools: ["AskUserQuestion"],
  };
}

/** Default agent settings. */
function defaultAgentSettings(): AgentSettings {
  return {
    autoDetect: true,
    targetAgents: [],
    symlinkSkills: true,
  };
}

/** Default provider settings. */
function defaultProviderSettings(): ProviderSettings {
  return {
    enabledProviders: ["skillssh"],
    wellknownDomains: [],
  };
}

/** The default configuration object. */
export const DEFAULT_CONFIG: Config = {
  detection: defaultDetectionConfig(),
  agents: defaultAgentSettings(),
  providers: defaultProviderSettings(),
  dbPath: null,
  skillsOutputDir: null,
  enabled: true,
};

/** Create a default Config object. */
function defaultConfig(): Config {
  return {
    detection: defaultDetectionConfig(),
    agents: defaultAgentSettings(),
    providers: defaultProviderSettings(),
    dbPath: null,
    skillsOutputDir: null,
    enabled: true,
  };
}

/**
 * Extract and parse YAML frontmatter from markdown content.
 *
 * @param content - Markdown content potentially containing YAML frontmatter.
 * @returns Parsed YAML data or null if no valid frontmatter found.
 */
export function parseYamlFrontmatter(
  content: string,
): Record<string, unknown> | null {
  if (!content.startsWith("---")) {
    return null;
  }

  const parts = content.split("---", 3);
  if (parts.length < 3) {
    return null;
  }

  try {
    const parsed = yaml.parse(parts[1]);
    return parsed ?? {};
  } catch {
    return null;
  }
}

/**
 * Build a DetectionConfig from a raw data object, falling back to defaults.
 */
function detectionConfigFromData(data: Record<string, unknown>): DetectionConfig {
  const defaults = defaultDetectionConfig();
  return {
    minOccurrences:
      typeof data.min_occurrences === "number"
        ? data.min_occurrences
        : defaults.minOccurrences,
    minSequenceLength:
      typeof data.min_sequence_length === "number"
        ? data.min_sequence_length
        : defaults.minSequenceLength,
    maxSequenceLength:
      typeof data.max_sequence_length === "number"
        ? data.max_sequence_length
        : defaults.maxSequenceLength,
    lookbackDays:
      typeof data.lookback_days === "number"
        ? data.lookback_days
        : defaults.lookbackDays,
    minConfidence:
      typeof data.min_confidence === "number"
        ? data.min_confidence
        : defaults.minConfidence,
    ignoredTools: Array.isArray(data.ignored_tools)
      ? data.ignored_tools
      : defaults.ignoredTools,
  };
}

/**
 * Build an AgentSettings from a raw data object, falling back to defaults.
 */
function agentSettingsFromData(data: Record<string, unknown>): AgentSettings {
  const defaults = defaultAgentSettings();
  return {
    autoDetect:
      typeof data.auto_detect === "boolean"
        ? data.auto_detect
        : defaults.autoDetect,
    targetAgents: Array.isArray(data.target_agents)
      ? data.target_agents
      : defaults.targetAgents,
    symlinkSkills:
      typeof data.symlink_skills === "boolean"
        ? data.symlink_skills
        : defaults.symlinkSkills,
  };
}

/**
 * Build a ProviderSettings from a raw data object, falling back to defaults.
 */
function providerSettingsFromData(
  data: Record<string, unknown>,
): ProviderSettings {
  const defaults = defaultProviderSettings();
  return {
    enabledProviders: Array.isArray(data.enabled_providers)
      ? data.enabled_providers
      : defaults.enabledProviders,
    wellknownDomains: Array.isArray(data.wellknown_domains)
      ? data.wellknown_domains
      : defaults.wellknownDomains,
  };
}

/**
 * Load configuration with optional project overrides.
 *
 * Loads defaults and merges any project-local overrides found in
 * `.claude/auto-skill.local.md`.
 *
 * @param projectPath - Path to project root for local overrides.
 * @returns Config with merged settings.
 */
export function loadConfig(projectPath?: string): Config {
  const config = defaultConfig();

  if (projectPath) {
    const localConfigPath = path.join(projectPath, LOCAL_CONFIG_FILE);
    try {
      if (fs.existsSync(localConfigPath)) {
        const content = fs.readFileSync(localConfigPath, "utf-8");
        const data = parseYamlFrontmatter(content);

        if (data) {
          if (
            typeof data.detection === "object" &&
            data.detection !== null &&
            !Array.isArray(data.detection)
          ) {
            config.detection = detectionConfigFromData(
              data.detection as Record<string, unknown>,
            );
          }

          if (
            typeof data.agents === "object" &&
            data.agents !== null &&
            !Array.isArray(data.agents)
          ) {
            config.agents = agentSettingsFromData(
              data.agents as Record<string, unknown>,
            );
          }

          if (
            typeof data.providers === "object" &&
            data.providers !== null &&
            !Array.isArray(data.providers)
          ) {
            config.providers = providerSettingsFromData(
              data.providers as Record<string, unknown>,
            );
          }

          if (typeof data.enabled === "boolean") {
            config.enabled = data.enabled;
          }
        }
      }
    } catch {
      // Failed to load local config; continue with defaults
    }
  }

  return config;
}
