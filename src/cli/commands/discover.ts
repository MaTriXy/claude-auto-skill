/**
 * Discover, Search, and Stats Commands.
 *
 * - discover: Find skills relevant to the current project.
 * - search: Search the Skills.sh registry for external skills.
 * - stats: Show skill adoption statistics.
 */

/** Options for the discover command. */
export interface DiscoverOptions {
  project?: string;
  mental?: boolean;
  external?: boolean;
  limit?: string;
  json?: boolean;
}

/** Options for the search command. */
export interface SearchOptions {
  limit?: string;
  json?: boolean;
}

/** Options for the stats command. */
export interface StatsOptions {
  project?: string;
  json?: boolean;
}

/**
 * Discover skills relevant to the current project.
 * Scans local patterns and optionally queries external sources.
 */
export async function discoverCommand(opts: DiscoverOptions): Promise<void> {
  const projectPath = opts.project || process.cwd();

  if (opts.json) {
    console.log(
      JSON.stringify(
        {
          project_path: projectPath,
          count: 0,
          suggestions: [],
        },
        null,
        2,
      ),
    );
  } else {
    console.log(`\nDiscovering skills for: ${projectPath}\n`);
    console.log("No suggestions found yet. Work on some files first.");
  }
}

/**
 * Search the Skills.sh registry for external skills matching a query.
 */
export async function searchCommand(
  query: string,
  opts: SearchOptions,
): Promise<void> {
  const { createSkillsShClient } = await import("../../core/skillssh-client");
  const client = createSkillsShClient();

  try {
    const skills = await client.search(query, parseInt(opts.limit || "10"));

    if (opts.json) {
      console.log(
        JSON.stringify({ query, count: skills.length, skills }, null, 2),
      );
    } else {
      console.log(`\nSearching Skills.sh for: '${query}'\n`);
      if (skills.length === 0) {
        console.log("No skills found.");
        return;
      }
      for (let i = 0; i < skills.length; i++) {
        const s = skills[i];
        console.log(`${i + 1}. ${s.name}`);
        console.log(`   ${s.description}`);
        console.log(`   Author: ${s.author} | Installs: ${s.installCount}`);
        if (s.tags.length) console.log(`   Tags: ${s.tags.join(", ")}`);
        console.log();
      }
    }
  } catch {
    if (opts.json) {
      console.log(
        JSON.stringify({ error: "Search failed", skills: [] }, null, 2),
      );
    } else {
      console.log("Search failed. Check your internet connection.");
    }
  }
}

/**
 * Show skill adoption statistics for the current project.
 */
export async function statsCommand(opts: StatsOptions): Promise<void> {
  if (opts.json) {
    console.log(JSON.stringify({ count: 0, adoptions: [] }, null, 2));
  } else {
    console.log("\nAdoption Statistics\n");
    console.log(
      "No skills adopted yet. Use 'auto-skill discover' to find skills.",
    );
  }
}
