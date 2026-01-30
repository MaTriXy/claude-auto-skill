/**
 * Web server entry point for Auto-Skill dashboard.
 *
 * Starts the Hono app on the specified port using the Node.js HTTP adapter.
 * Can be run directly or imported and started programmatically.
 */
import { serve } from "@hono/node-server";
import { createApp } from "./app";

/**
 * Starts the Auto-Skill web server on the given port.
 *
 * @param port - The port number to listen on (default: 5000)
 */
export function startWebServer(port: number = 5000): void {
  const app = createApp();

  console.log("Auto-Skill Web UI");
  console.log(`Starting server on http://localhost:${port}`);
  console.log();

  serve({ fetch: app.fetch, port });
}

// Allow running directly
if (require.main === module) {
  const port = parseInt(process.env.PORT || "5000");
  startWebServer(port);
}
