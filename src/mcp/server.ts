/**
 * MCP Server - Model Context Protocol server for auto-skill.
 *
 * Exposes skill search and retrieval as MCP tools that can be
 * used by AI coding agents that support the MCP protocol.
 *
 * Tools:
 * - search_skills: Search for skills by query
 * - get_skill: Get details for a specific skill
 * - list_skills: List all available skills
 * - skill_stats: Get adoption statistics
 */
import http from "node:http";

export interface McpTool {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
}

export interface McpRequest {
  jsonrpc: "2.0";
  id: number | string;
  method: string;
  params?: Record<string, unknown>;
}

export interface McpResponse {
  jsonrpc: "2.0";
  id: number | string;
  result?: unknown;
  error?: { code: number; message: string };
}

const TOOLS: McpTool[] = [
  {
    name: "search_skills",
    description: "Search for skills by query string. Returns matching skills from local, external, and well-known sources.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "Search query" },
        limit: { type: "number", description: "Max results (default: 10)" },
        source: { type: "string", enum: ["all", "local", "external", "wellknown"], description: "Source filter" },
      },
      required: ["query"],
    },
  },
  {
    name: "get_skill",
    description: "Get detailed information about a specific skill by name or ID.",
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string", description: "Skill name or ID" },
      },
      required: ["name"],
    },
  },
  {
    name: "list_skills",
    description: "List all available skills with optional filtering.",
    inputSchema: {
      type: "object",
      properties: {
        collection: { type: "string", enum: ["all", "auto", "local", "external", "graduated"], description: "Collection filter" },
        limit: { type: "number", description: "Max results (default: 50)" },
      },
    },
  },
  {
    name: "skill_stats",
    description: "Get adoption statistics for skills.",
    inputSchema: {
      type: "object",
      properties: {
        skillName: { type: "string", description: "Optional skill name filter" },
      },
    },
  },
];

/** Handle a tool call by dispatching to the appropriate provider. */
async function handleToolCall(name: string, args: Record<string, unknown>): Promise<unknown> {
  switch (name) {
    case "search_skills": {
      // Lazy load to avoid circular deps
      const { createProviderManager } = await import("../core/providers/manager");
      const { createLocalProvider } = await import("../core/providers/local-provider");
      const manager = createProviderManager();
      manager.register(createLocalProvider());
      const results = await manager.searchAll(
        args.query as string,
        (args.limit as number) || 10
      );
      return { count: results.length, skills: results };
    }

    case "get_skill": {
      const { createProviderManager } = await import("../core/providers/manager");
      const { createLocalProvider } = await import("../core/providers/local-provider");
      const manager = createProviderManager();
      manager.register(createLocalProvider());
      const result = await manager.getSkillDetails(args.name as string);
      return result || { error: "Skill not found" };
    }

    case "list_skills": {
      const { createLocalProvider } = await import("../core/providers/local-provider");
      const provider = createLocalProvider();
      const results = await provider.search("", (args.limit as number) || 50);
      return { count: results.length, skills: results };
    }

    case "skill_stats": {
      return { message: "Stats endpoint - connect to telemetry DB for data" };
    }

    default:
      return { error: `Unknown tool: ${name}` };
  }
}

/** Handle an incoming JSON-RPC request and return a response. */
function handleRequest(req: McpRequest): McpResponse {
  const base = { jsonrpc: "2.0" as const, id: req.id };

  switch (req.method) {
    case "initialize":
      return {
        ...base,
        result: {
          protocolVersion: "2024-11-05",
          capabilities: { tools: {} },
          serverInfo: { name: "auto-skill", version: "4.0.1" },
        },
      };

    case "tools/list":
      return { ...base, result: { tools: TOOLS } };

    case "tools/call": {
      const params = req.params || {};
      const name = params.name as string;
      const args = (params.arguments || {}) as Record<string, unknown>;

      // Note: In production, this would be async
      // For simplicity, we return a sync stub
      return {
        ...base,
        result: {
          content: [{ type: "text", text: JSON.stringify({ tool: name, args, status: "queued" }) }],
        },
      };
    }

    default:
      return { ...base, error: { code: -32601, message: `Unknown method: ${req.method}` } };
  }
}

/** Create and start the MCP server (stdio transport). */
export function startMcpServer(): void {
  const readline = require("node:readline");
  const rl = readline.createInterface({ input: process.stdin });

  rl.on("line", (line: string) => {
    try {
      const req = JSON.parse(line) as McpRequest;
      const response = handleRequest(req);
      process.stdout.write(JSON.stringify(response) + "\n");
    } catch (err) {
      const errorResponse: McpResponse = {
        jsonrpc: "2.0",
        id: 0,
        error: { code: -32700, message: "Parse error" },
      };
      process.stdout.write(JSON.stringify(errorResponse) + "\n");
    }
  });
}

/** Create MCP server for HTTP transport (for web UI). */
export function createMcpHttpServer(port: number = 3001): http.Server {
  const server = http.createServer(async (req, res) => {
    if (req.method !== "POST") {
      res.writeHead(405).end("Method not allowed");
      return;
    }

    const chunks: Buffer[] = [];
    req.on("data", (chunk: Buffer) => chunks.push(chunk));
    req.on("end", () => {
      try {
        const body = Buffer.concat(chunks).toString();
        const mcpReq = JSON.parse(body) as McpRequest;
        const response = handleRequest(mcpReq);
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify(response));
      } catch {
        res.writeHead(400).end("Bad request");
      }
    });
  });

  server.listen(port, () => {
    console.log(`MCP HTTP server listening on port ${port}`);
  });

  return server;
}

export { TOOLS, handleToolCall, handleRequest };
