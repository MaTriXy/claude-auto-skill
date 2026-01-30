/**
 * Barrel export for the web UI module.
 *
 * Re-exports the Hono app factory, configuration, and server starter.
 */
export { createApp, CONFIG } from "./app";
export { startWebServer } from "./server";
