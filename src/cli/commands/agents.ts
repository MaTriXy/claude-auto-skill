/**
 * Agents Command - Manage and inspect coding agent configurations.
 *
 * Lists known agents, detects installed agents, and shows their skill directories.
 */
import { createAgentRegistry } from "../../core/agent-registry";

/** Options for the agents command. */
export interface AgentsOptions {
  json?: boolean;
}

/**
 * Manage agent configurations.
 * @param action - "list" (default) to show all agents, "detect" to find installed ones.
 * @param opts - Command options.
 */
export async function agentsCommand(
  action: string,
  opts: AgentsOptions,
): Promise<void> {
  const registry = createAgentRegistry();

  if (action === "detect") {
    const installed = registry.detectInstalledAgents();
    if (opts.json) {
      console.log(
        JSON.stringify(
          {
            count: installed.length,
            agents: installed.map((a) => ({
              id: a.id,
              name: a.name,
              skillDir: a.skillDir,
            })),
          },
          null,
          2,
        ),
      );
    } else {
      console.log(`\nDetected Agents (${installed.length} installed)\n`);
      for (const a of installed) {
        console.log(`  ${a.name} (${a.id})`);
        console.log(`     Skills: ${a.skillDir}\n`);
      }
    }
  } else {
    // list (default)
    const agents = registry.listAgents();
    if (opts.json) {
      console.log(
        JSON.stringify(
          {
            count: agents.length,
            agents: agents.map((a) => ({
              id: a.id,
              name: a.name,
              skillDir: a.skillDir,
              installed: registry
                .detectInstalledAgents()
                .some((i) => i.id === a.id),
              description: a.description,
            })),
          },
          null,
          2,
        ),
      );
    } else {
      console.log(`\nKnown Agents (${agents.length} total)\n`);
      const installed = new Set(
        registry.detectInstalledAgents().map((a) => a.id),
      );
      for (const a of agents) {
        const status = installed.has(a.id) ? "[installed]" : "[not found]";
        console.log(`  ${status} ${a.name} (${a.id})`);
        console.log(`     Skills: ${a.skillDir}`);
        if (a.description) console.log(`     ${a.description}`);
        console.log();
      }
    }
  }
}
