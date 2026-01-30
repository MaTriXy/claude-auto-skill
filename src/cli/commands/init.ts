/**
 * Init Command - Initialize auto-skill configuration and directories.
 *
 * Creates the necessary directory structure, config file,
 * and checks for optional dependencies.
 */
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { execSync } from "node:child_process";

const DEFAULT_CONFIG = `---
detection:
  min_occurrences: 3
  min_sequence_length: 2
  max_sequence_length: 10
  lookback_days: 7
  min_confidence: 0.7
  ignored_tools:
    - AskUserQuestion

hybrid:
  enable_mental: true
  enable_external: true
  auto_graduate: true

enabled: true
---

# Auto-Skill Configuration
`;

/** Options for the init command. */
export interface InitOptions {
  force?: boolean;
  json?: boolean;
}

/**
 * Initialize auto-skill by creating directories, config, and checking deps.
 */
export async function initCommand(opts: InitOptions): Promise<void> {
  const home = os.homedir();
  const claudeDir = path.join(home, ".claude");
  const autoskillDir = path.join(claudeDir, "auto-skill");
  const skillsDir = path.join(claudeDir, "skills", "auto");
  const configPath = path.join(claudeDir, "auto-skill.local.md");

  const created: string[] = [];

  // Create directories
  const dirs: Array<[string, string]> = [
    [claudeDir, "Claude directory"],
    [autoskillDir, "Auto-Skill data"],
    [skillsDir, "Skills output"],
  ];

  for (const [dir, desc] of dirs) {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
      created.push(dir);
      if (!opts.json) console.log(`  Created ${desc}: ${dir}`);
    }
  }

  // Create config
  if (!fs.existsSync(configPath) || opts.force) {
    fs.writeFileSync(configPath, DEFAULT_CONFIG);
    created.push(configPath);
    if (!opts.json) console.log(`  Created config: ${configPath}`);
  }

  // Check dependencies
  if (!opts.json) {
    console.log("\nChecking dependencies:");
    try {
      execSync("mental --version", { stdio: "pipe" });
      console.log("  Mental CLI: installed");
    } catch {
      console.log("  Mental CLI: not found (npm i -g @mentalmodel/cli)");
    }
  }

  if (opts.json) {
    console.log(JSON.stringify({ created, success: true }, null, 2));
  } else {
    console.log("\nInitialization complete!");
    console.log("Run 'auto-skill discover' to find skills.");
  }
}
