import { describe, it, expect } from "vitest";
import { createAgentRegistry } from "../src/core/agent-registry";

describe("AgentRegistry", () => {
  it("lists known agents", () => {
    const registry = createAgentRegistry();
    const agents = registry.listAgents();
    expect(agents.length).toBeGreaterThanOrEqual(10);
  });

  it("gets agent by ID", () => {
    const registry = createAgentRegistry();
    const agent = registry.getAgent("claude-code");
    expect(agent).not.toBeNull();
    expect(agent!.name).toBe("Claude Code");
  });

  it("returns null for unknown agent", () => {
    const registry = createAgentRegistry();
    expect(registry.getAgent("nonexistent")).toBeNull();
  });

  it("registers custom agent", () => {
    const registry = createAgentRegistry();
    registry.registerAgent({
      id: "custom",
      name: "Custom Agent",
      skillDir: "/tmp/custom/skills",
      description: "Test agent",
    });
    expect(registry.getAgent("custom")).not.toBeNull();
  });

  it("unregisters agent", () => {
    const registry = createAgentRegistry();
    registry.registerAgent({ id: "temp", name: "Temp", skillDir: "/tmp", description: "" });
    expect(registry.unregisterAgent("temp")).toBe(true);
    expect(registry.unregisterAgent("temp")).toBe(false);
  });
});
