/**
 * Telemetry Command - View usage telemetry and skill effectiveness reports.
 *
 * Supports viewing raw events and aggregated effectiveness reports
 * with optional filtering by skill name.
 */

/** Options for the telemetry command. */
export interface TelemetryOptions {
  skill?: string;
  limit?: string;
  json?: boolean;
}

/**
 * View telemetry data.
 * @param action - "report" (default) or "events".
 * @param opts - Command options.
 */
export async function telemetryCommand(
  action: string,
  opts: TelemetryOptions,
): Promise<void> {
  const { createTelemetryCollector } = await import("../../core/telemetry");
  const collector = createTelemetryCollector();

  if (action === "events") {
    const events = collector.getEvents(
      opts.skill,
      parseInt(opts.limit || "20"),
    );
    if (opts.json) {
      console.log(
        JSON.stringify({ count: events.length, events }, null, 2),
      );
    } else {
      console.log(`\nTelemetry Events (latest ${events.length})\n`);
      for (const e of events) {
        const icon = e.outcome === "success" ? "OK" : "FAIL";
        const dur = e.durationMs ? ` (${e.durationMs}ms)` : "";
        console.log(`  [${icon}] ${e.skillName} [${e.agentId}]${dur}`);
        console.log(
          `     Session: ${e.sessionId.slice(0, 12)}... | ${e.timestamp}`,
        );
      }
    }
  } else {
    // report (default)
    const reports = collector.getEffectivenessReport(opts.skill);
    if (opts.json) {
      console.log(
        JSON.stringify({ count: reports.length, reports }, null, 2),
      );
    } else {
      console.log("\nSkill Effectiveness Report\n");
      if (!reports.length) {
        console.log("  No telemetry data yet.");
        return;
      }
      for (const r of reports) {
        console.log(`  ${r.skillName}`);
        console.log(
          `    Uses: ${r.totalUses} | Success: ${(r.successRate * 100).toFixed(0)}%`,
        );
        if (r.avgDurationMs)
          console.log(`    Avg Duration: ${r.avgDurationMs.toFixed(0)}ms`);
        console.log(`    Agents: ${r.agentsUsed.join(", ")}`);
        console.log();
      }
    }
  }
}
