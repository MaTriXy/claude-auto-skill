# Auto-Skill: Python → Node/Bun Migration Plan

> **Version**: 2.0 — Final consolidated plan (with qmd-inspired storage & MCP)
> **Target release**: v4.0.0
> **Scope**: Full rewrite of ~50 Python files to TypeScript, shipping as a pure npm package
> **Informed by**: `a5c-ai/babysitter` (build infra, patterns) + `MaTriXy/qmd` (storage, search, MCP)

---

## Table of Contents

1. [Design Decisions](#1-design-decisions)
2. [Project Scaffolding & Build Infra](#2-project-scaffolding--build-infra)
3. [Directory Structure](#3-directory-structure)
4. [Core Module Migration (Dependency Order)](#4-core-module-migration-dependency-order)
5. [Hooks System Migration](#5-hooks-system-migration)
6. [CLI Migration](#6-cli-migration)
7. [Web UI Migration](#7-web-ui-migration)
8. [Scripts Migration](#8-scripts-migration)
9. [Test Suite Migration](#9-test-suite-migration)
10. [Dependency Map](#10-dependency-map)
11. [Distribution Changes](#11-distribution-changes)
12. [CI/CD](#12-cicd)
13. [Bun Compatibility](#13-bun-compatibility)
14. [FTS5 Skill Store & Content-Addressable Storage](#14-fts5-skill-store--content-addressable-storage)
15. [MCP Server](#15-mcp-server)
16. [Cleanup & Removal](#16-cleanup--removal)
17. [Execution Order](#17-execution-order)
18. [Risk Areas](#18-risk-areas)

---

## 1. Design Decisions

Key architectural decisions, informed by analysis of `a5c-ai/babysitter` (build infra) and `MaTriXy/qmd` (storage & search).

### Build & Runtime (from babysitter)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Module format** | **CommonJS** | Babysitter ships CJS successfully. Avoids ESM interop pain with native addons (`better-sqlite3`) and older tooling. Node 18+ still runs CJS natively. |
| **Build tool** | **Plain `tsc`** (no bundler) | Babysitter proves `tsc` → `dist/` works fine. No tsup, esbuild, or webpack. Simpler build, easier debugging, source maps just work. |
| **Package structure** | **Single package** (defer monorepo) | Start as one package with `"bin"` + `"main"` + `"types"` exports. Split into metapackage + SDK later only if programmatic API consumers emerge. |
| **CLI framework** | **`commander`** with factory pattern | Export `createCli()` returning `{ run(argv) }` — unit-testable without spawning processes (babysitter pattern). |
| **Identifiers** | **ULID** (not UUID) | Lexicographically sortable, chronological ordering as strings. Same as babysitter. Replaces Python's `uuid4()`. |
| **File writes** | **Atomic write utility** | Write to temp file (PID+timestamp suffix), fsync, rename. Retry on EBUSY/EPERM with exponential backoff. Adopted from babysitter's `writeFileAtomic()`. |
| **Hook failures** | **Graceful degradation** | Hook errors are logged but never throw. The system continues. Adopted from babysitter's runtime hook pattern. |
| **Storage versioning** | **Layout version constant** | Storage paths include a version string (e.g., `"2026.01-v4"`) enabling future on-disk format migrations without breaking existing data. |
| **Linting** | **ESLint + `@typescript-eslint`** | Proven combo, type-aware linting. Babysitter validates this works well at scale. |
| **Testing** | **Vitest** | Fast, native ESM/CJS support, great DX, built-in mocking. Same choice as babysitter. |
| **Web framework** | **Hono** | Ultralight (~14KB), runs on Node and Bun. The dashboard is simple enough that a full framework like Express/Fastify is overkill. |

### Storage & Search (from qmd)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **SQLite driver** | **`better-sqlite3`** + **WAL mode** + **foreign keys** | Synchronous API, fast, well-maintained. qmd validates this stack for both event storage and full-text search. WAL mode enables concurrent reads. |
| **Skill search** | **SQLite FTS5** with BM25 ranking | Replaces naive JS tokenizer with real full-text search. qmd's `store.ts` proves FTS5 virtual tables + auto-sync triggers are production-ready. Orders of magnitude better than in-memory keyword scoring. |
| **Content storage** | **Content-addressable** (SHA-256 keyed) | Skills stored by content hash with deduplication. Same pattern as qmd's `content` table. Enables integrity verification and efficient storage. |
| **Skill collections** | **Collection-based organization** | Skills organized into collections (`auto`, `local`, `external`, `graduated`). Mirrors qmd's multi-collection model with per-collection context. |
| **Semantic search** | **sqlite-vec** (optional/advanced) | Vector similarity search for semantic skill matching. Optional dependency — FTS5 is the baseline. sqlite-vec provides cosine similarity when embeddings are available. |
| **Agent integration** | **MCP server** | Expose skill search, retrieval, and stats as MCP tools. Any MCP-compatible agent (Claude Desktop, Claude Code, etc.) can search skills. Adopted from qmd's MCP architecture. |
| **Output formats** | **Multi-format** (JSON, CSV, MD) | CLI and API support multiple output formats. Adopted from qmd's `formatter.ts` pattern. |
| **DB connection setup** | **qmd-style initialization** | WAL journal mode, foreign keys enabled, `CREATE TABLE IF NOT EXISTS` with auto-sync triggers. Same proven setup as qmd. |

### Not adopted from qmd

| qmd feature | Decision | Reason |
|---|---|---|
| `node-llama-cpp` / GGUF models | **Skip** | ~2GB of local models is too heavy for a plugin. Auto-skill must stay lightweight. |
| Hybrid search with LLM reranking | **Skip** (for now) | Over-engineered for skill search at current scale. FTS5 + optional sqlite-vec is sufficient. |
| Query expansion | **Skip** | Needs a local LLM. Not appropriate for a zero-config plugin. |
| Bun-only APIs (`Bun.file()`, etc.) | **Skip** | We need Node + Bun compat. Use `node:fs` everywhere. |
| Chunking system (800 tokens, 15% overlap) | **Defer** | Only needed if/when we add vector embeddings for skills. Not needed for FTS5. |

---

## 2. Project Scaffolding & Build Infra

### 2.1 — package.json

```jsonc
{
  "name": "auto-skill",
  "version": "4.0.0",
  "description": "Automatically learn from your workflows and turn them into intelligent, context-aware skills",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "bin": {
    "auto-skill": "bin/auto-skill.js"
  },
  "files": [
    "dist",
    "bin",
    "hooks",
    "skills",
    "commands/*.md"
  ],
  "scripts": {
    "build": "tsc",
    "clean": "rimraf dist",
    "dev": "tsx src/cli/cli.ts",
    "test": "vitest run",
    "test:watch": "vitest",
    "lint": "eslint src/ tests/ --max-warnings=0",
    "typecheck": "tsc --noEmit",
    "mcp": "tsx src/cli/cli.ts mcp",
    "prepublishOnly": "npm run clean && npm run build"
  },
  "engines": {
    "node": ">=18"
  }
}
```

### 2.2 — bin/auto-skill.js (thin entry point)

```js
#!/usr/bin/env node
"use strict";
const { createCli } = require("../dist/cli/cli.js");
void createCli().run(process.argv);
```

This follows babysitter's metapackage pattern — the bin file contains zero logic, just imports and calls.

### 2.3 — tsconfig.json

```jsonc
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "moduleResolution": "node",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true
  },
  "include": ["src"],
  "exclude": ["src/**/__tests__", "src/**/*.test.ts"]
}
```

Key choices matching babysitter: CJS output, ES2022 target, strict mode, declaration files for consumers.

### 2.4 — vitest.config.ts

```ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    globals: false,
    include: ["tests/**/*.test.ts"],
    testTimeout: 10000,
  },
});
```

### 2.5 — ESLint config

```jsonc
// eslint.config.js — flat config
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended-type-checked"
  ],
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "project": "./tsconfig.json"
  }
}
```

### 2.6 — .gitignore additions

```
dist/
node_modules/
*.tsbuildinfo
```

---

## 3. Directory Structure

```
auto-skill/
├── bin/
│   └── auto-skill.js          # Thin CLI entry point (CJS, no logic)
├── src/
│   ├── index.ts                # Public API exports (for programmatic use)
│   ├── types/
│   │   └── index.ts            # All shared interfaces, types, Zod schemas
│   ├── util/
│   │   ├── atomic-write.ts     # Atomic file write with retry (from babysitter)
│   │   ├── ulid.ts             # ULID generation wrapper
│   │   ├── fs.ts               # Common filesystem helpers
│   │   └── fts.ts              # FTS5 query sanitizer (from qmd)
│   ├── cli/
│   │   ├── cli.ts              # createCli() factory (from babysitter pattern)
│   │   ├── init.ts             # auto-skill init
│   │   ├── discover.ts         # auto-skill discover
│   │   ├── search.ts           # auto-skill search (FTS5-backed)
│   │   ├── agents.ts           # auto-skill agents
│   │   ├── lock.ts             # auto-skill lock
│   │   ├── telemetry.ts        # auto-skill telemetry
│   │   └── mcp.ts              # auto-skill mcp (start MCP server)
│   ├── core/
│   │   ├── db.ts               # DB factory: WAL, foreign keys, extension loading (from qmd)
│   │   ├── config.ts           # Configuration management
│   │   ├── event-store.ts      # SQLite event persistence
│   │   ├── skill-store.ts      # NEW — Content-addressable skill storage + FTS5 (from qmd)
│   │   ├── migrations.ts       # DB schema versioning (events + skills + FTS5 + triggers)
│   │   ├── lock-file.ts        # Skill integrity (SHA-256 + atomic writes)
│   │   ├── path-security.ts    # Path traversal prevention
│   │   ├── pattern-detector.ts # Pattern recognition (v1+v2)
│   │   ├── sequence-matcher.ts # Subsequence detection algorithm
│   │   ├── session-analyzer.ts # Session context analysis
│   │   ├── design-pattern-detector.ts # 18 design patterns
│   │   ├── lsp-analyzer.ts     # Code structure analysis
│   │   ├── skill-generator.ts  # SKILL.md generation
│   │   ├── spec-validator.ts   # agentskills.io compliance
│   │   ├── agent-registry.ts   # Multi-agent detection + symlinks
│   │   ├── skill-tracker.ts    # Usage adoption tracking (SQLite)
│   │   ├── graduation-manager.ts # External→local promotion
│   │   ├── unified-suggester.ts  # Hybrid skill discovery (FTS5 + providers)
│   │   ├── skillssh-client.ts  # Skills.sh API client
│   │   ├── skillssh-publisher.ts # Skills.sh publishing
│   │   ├── mental-analyzer.ts  # Mental model integration
│   │   ├── telemetry.ts        # Anonymous telemetry beacon
│   │   └── providers/
│   │       ├── base.ts         # Provider interface
│   │       ├── manager.ts      # Provider orchestration
│   │       ├── skillssh.ts     # Skills.sh provider
│   │       ├── local.ts        # Local filesystem provider
│   │       └── wellknown.ts    # RFC 8615 discovery
│   ├── hooks/
│   │   └── observer.ts         # Hook observer (record + analyze)
│   ├── mcp/
│   │   └── server.ts           # NEW — MCP server (skill search, retrieval, stats) (from qmd)
│   ├── scripts/
│   │   ├── skill-registry.ts   # Skill indexing
│   │   ├── search-skills.ts    # Skill search (now delegates to FTS5)
│   │   ├── get-skill.ts        # Load skill content
│   │   ├── discover-skill.ts   # Skill discovery
│   │   └── list-skills.ts      # List available skills
│   ├── formatter/
│   │   └── index.ts            # NEW — Multi-format output (JSON, CSV, MD) (from qmd)
│   └── web/
│       ├── app.ts              # Hono server + API routes
│       └── templates/
│           └── index.html      # Dashboard (static, carried over)
├── hooks/
│   └── hooks.json              # Agent hook definitions (points to node)
├── skills/                     # Plugin skills (SKILL.md files, unchanged)
├── commands/                   # Slash commands (*.md files, unchanged)
├── tests/
│   ├── event-store.test.ts
│   ├── skill-store.test.ts     # NEW — FTS5 search, content-addressable storage
│   ├── pattern-detector.test.ts
│   ├── skill-generator.test.ts
│   ├── agent-registry.test.ts
│   ├── lock-file.test.ts
│   ├── migrations.test.ts
│   ├── path-security.test.ts
│   ├── providers.test.ts
│   ├── mcp-server.test.ts      # NEW — MCP tool tests
│   ├── multi-agent-output.test.ts
│   ├── edge-cases.test.ts
│   ├── v2-integration.test.ts
│   ├── phase3-integration.test.ts
│   ├── performance.test.ts
│   ├── spec-compliance.test.ts
│   ├── telemetry.test.ts
│   ├── sequence-matcher.test.ts
│   └── wellknown-provider.test.ts
├── .claude-plugin/
│   └── plugin.json             # Updated hook commands
├── website/                    # Docusaurus (already Node, content updates only)
├── package.json
├── tsconfig.json
├── vitest.config.ts
├── eslint.config.js
└── .github/workflows/          # Node CI + npm publish
```

---

## 4. Core Module Migration (Dependency Order)

Migrate bottom-up. Each layer depends only on layers below it.

### Layer 0 — Types, Utilities, Pure Logic (zero internal deps)

| Python Source | TypeScript Target | Migration Notes |
|---------------|-------------------|-----------------|
| Dataclasses scattered across files | `src/types/index.ts` | Consolidate all interfaces. Add Zod schemas for runtime validation at system boundaries (config loading, stdin parsing). |
| `core/path_security.py` (177 lines) | `src/core/path-security.ts` | `node:path` for path ops, `node:fs` for realpath/symlink checks. Logic is 1:1 portable. |
| `core/config.py` (160 lines) | `src/core/config.ts` | `yaml` npm package replaces PyYAML. Same structure: defaults + project overrides. |
| `core/spec_validator.py` (60 lines) | `src/core/spec-validator.ts` | Pure string validation. Direct port. |
| _(new)_ | `src/util/atomic-write.ts` | **Adopted from babysitter**: write temp file → fsync → rename → fsync dir. Retry on EBUSY/ETXTBSY/EPERM/EACCES with exponential backoff. |
| _(new)_ | `src/util/ulid.ts` | **Adopted from babysitter**: ULID generation for event/pattern IDs. Replaces `uuid.uuid4()`. |

### Layer 1 — Storage (depends on Layer 0)

| Python Source | TypeScript Target | Migration Notes |
|---------------|-------------------|-----------------|
| _(new)_ | `src/core/db.ts` | **Database factory adopted from qmd.** Opens SQLite with WAL journal mode, foreign keys enabled, `PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;`. Handles Bun vs Node driver detection (see Section 13). Loads sqlite-vec extension when available. Single factory function: `openDatabase(path): Database`. |
| `core/event_store.py` (100+ lines) | `src/core/event-store.ts` | Uses `db.ts` factory. Same schema: `tool_events` table with session_id, project_path, timestamp, tool_name indexes. Use ULID for event IDs. |
| _(new)_ | `src/core/skill-store.ts` | **New module adopted from qmd's `store.ts` pattern.** Content-addressable skill storage with FTS5 full-text search. Three tables: `skill_content` (hash-keyed bodies), `skills` (metadata + collection), `skills_fts` (FTS5 virtual table). Auto-sync triggers keep FTS index current. See [Section 14](#14-fts5-skill-store--content-addressable-storage) for full schema and API. |
| `core/migrations.py` (501 lines) | `src/core/migrations.ts` | Same pattern: `schema_version` table, ordered migration functions. Now includes FTS5 virtual table creation, trigger creation, and optional sqlite-vec vector table setup. Consider also supporting sequential SQL files like babysitter's `001_init.sql` approach. |
| `core/lock_file.py` (60 lines) | `src/core/lock-file.ts` | `node:crypto` for SHA-256. Use atomic-write utility for lock file writes. Content-addressable hashing matches qmd's SHA-256 approach. |
| `core/skill_tracker.py` (60 lines) | `src/core/skill-tracker.ts` | Uses `db.ts` factory. Same schema. |

**Storage versioning**: Add a `STORAGE_LAYOUT_VERSION` constant (e.g., `"2026.01-v4"`) to all storage paths. This enables future format migrations (adopted from babysitter).

**Database connection setup** (from qmd):
```ts
// src/core/db.ts
export function openDatabase(dbPath: string): Database {
  const db = new BetterSqlite3(dbPath);

  // qmd-style initialization: WAL mode for concurrent reads, foreign keys enforced
  db.pragma("journal_mode = WAL");
  db.pragma("foreign_keys = ON");

  // Optional: load sqlite-vec extension for vector search
  try {
    const vecPath = require("sqlite-vec").getLoadablePath();
    db.loadExtension(vecPath);
  } catch {
    // sqlite-vec not installed — FTS5 still works, vector search disabled
  }

  return db;
}
```

### Layer 2 — Analysis (depends on Layers 0–1)

| Python Source | TypeScript Target | Migration Notes |
|---------------|-------------------|-----------------|
| `core/sequence_matcher.py` (60 lines) | `src/core/sequence-matcher.ts` | Pure algorithm (sliding window). Direct port. |
| `core/session_analyzer.py` (80 lines) | `src/core/session-analyzer.ts` | String matching + intent classification. Direct port. |
| `core/design_pattern_detector.py` (80 lines) | `src/core/design-pattern-detector.ts` | Regex + heuristic based. Direct port. |
| `core/lsp_analyzer.py` (80 lines) | `src/core/lsp-analyzer.ts` | **Biggest migration effort.** Replace Python AST module with `@typescript-eslint/parser` for JS/TS analysis. Replace `tree-sitter` Python bindings with `web-tree-sitter` (WASM). Replace `pygls` with `vscode-languageserver-protocol` types. |
| `core/pattern_detector.py` (100+ lines) | `src/core/pattern-detector.ts` | Integrates all Layer 2 modules. Port orchestration logic. |

### Layer 3 — Generation & Tracking (depends on Layers 0–2)

| Python Source | TypeScript Target | Migration Notes |
|---------------|-------------------|-----------------|
| `core/skill_generator.py` (80 lines) | `src/core/skill-generator.ts` | Template literals replace f-strings. Use atomic-write for skill file output. |
| `core/graduation_manager.py` (60 lines) | `src/core/graduation-manager.ts` | Pure threshold logic. Direct port. |
| `core/agent_registry.py` (80 lines) | `src/core/agent-registry.ts` | `node:fs` for path detection, `node:os` for homedir. `fs.symlinkSync` for cross-agent sharing. |
| `core/telemetry.py` (80 lines) | `src/core/telemetry.ts` | Native `fetch()` (Node 18+) replaces urllib/requests. Same privacy-first design. |

### Layer 4 — Discovery & Integration (depends on Layers 0–3)

| Python Source | TypeScript Target | Migration Notes |
|---------------|-------------------|-----------------|
| `core/skillssh_client.py` (80 lines) | `src/core/skillssh-client.ts` | Native `fetch()` for HTTP. Direct port. |
| `core/skillssh_publisher.py` (60 lines) | `src/core/skillssh-publisher.ts` | Native `fetch()`. Direct port. |
| `core/mental_analyzer.py` (60 lines) | `src/core/mental-analyzer.ts` | `node:child_process.execSync()` replaces `subprocess.run()`. |
| `core/providers/base.py` (91 lines) | `src/core/providers/base.ts` | TypeScript interface replaces Python Protocol. |
| `core/providers/manager.py` (115 lines) | `src/core/providers/manager.ts` | Promise-based parallel provider queries. |
| `core/providers/skillssh_provider.py` (56 lines) | `src/core/providers/skillssh.ts` | Thin adapter. Direct port. |
| `core/providers/local_provider.py` (60 lines) | `src/core/providers/local.ts` | `node:fs` + glob for skill discovery. |
| `core/providers/wellknown_provider.py` (60 lines) | `src/core/providers/wellknown.ts` | Native `fetch()` + in-memory cache (Map with TTL). |
| `core/unified_suggester.py` (60 lines) | `src/core/unified-suggester.ts` | **Upgraded**: Now uses FTS5 via `skill-store.ts` as primary search backend instead of in-memory keyword matching. Falls back to provider-based search for external sources. Aggregates FTS5 local results + Skills.sh + well-known providers with confidence-weighted ranking. |

---

## 5. Hooks System Migration

### 5.1 — Observer

Port `hooks/observer.py` → `src/hooks/observer.ts`.

Stdin reading in Node:
```ts
// Read JSON from stdin (same as Python's sys.stdin.read())
const chunks: Buffer[] = [];
for await (const chunk of process.stdin) chunks.push(chunk);
const input = JSON.parse(Buffer.concat(chunks).toString());
```

Two modes (same as current Python):
- `node dist/hooks/observer.js record` — save tool event to SQLite
- `node dist/hooks/observer.js analyze` — run pattern detection on session end

### 5.2 — hooks.json update

```json
{
  "hooks": [
    {
      "type": "PostToolUse",
      "command": "node \"$CLAUDE_PROJECT_ROOT/dist/hooks/observer.js\" record",
      "description": "Record tool usage events for pattern detection"
    },
    {
      "type": "Stop",
      "command": "node \"$CLAUDE_PROJECT_ROOT/dist/hooks/observer.js\" analyze",
      "description": "Analyze session for patterns when Claude stops"
    }
  ]
}
```

### 5.3 — Hook failure handling

**Adopted from babysitter**: Wrap all hook execution in try/catch. Log errors to stderr but **never exit with non-zero code**. The agent must not be disrupted by hook failures.

```ts
try {
  await main();
} catch (err) {
  console.error(`[auto-skill] hook error: ${err}`);
  process.exit(0); // Always exit clean — never break the agent
}
```

### 5.4 — No bundling needed

Since we use plain `tsc`, the compiled observer lands at `dist/hooks/observer.js`. The `better-sqlite3` native addon resolves from `node_modules/` at runtime. The hook command runs from the project root where `node_modules/` exists, so this works without bundling.

---

## 6. CLI Migration

### 6.1 — Factory pattern (from babysitter)

```ts
// src/cli/cli.ts
export function createCli() {
  return {
    async run(argv: string[] = process.argv) {
      const program = new Command();
      program.name("auto-skill").version("4.0.0");

      program.command("init").description("Initialize auto-skill").action(initCommand);
      program.command("search").description("Search skills (FTS5)").action(searchCommand);
      program.command("discover").description("Discover skills").action(discoverCommand);
      program.command("agents").description("Manage agents").action(agentsCommand);
      program.command("lock").description("Lock file management").action(lockCommand);
      program.command("telemetry").description("View telemetry").action(telemetryCommand);
      program.command("stats").description("Show statistics").action(statsCommand);
      program.command("mcp").description("Start MCP server").action(mcpCommand);
      program.command("version").description("Show version").action(versionCommand);

      await program.parseAsync(argv);
    }
  };
}
```

This is directly testable:
```ts
test("init command creates config", async () => {
  const cli = createCli();
  await cli.run(["node", "auto-skill", "init"]);
  // assert files created...
});
```

### 6.2 — Command files (1:1 port)

| Python | TypeScript | Notes |
|--------|-----------|-------|
| `commands/cli.py` (169 lines) | `src/cli/cli.ts` | Commander + factory |
| `commands/init.py` (275 lines) | `src/cli/init.ts` | `node:fs` for dir creation |
| `commands/discover.py` (100 lines) | `src/cli/discover.ts` | |
| _(new)_ | `src/cli/search.ts` | **New**: FTS5-backed skill search. `auto-skill search "query" [--collection X] [--limit N] [--format json\|csv\|md]`. Delegates to `skill-store.searchSkills()`. (from qmd) |
| `commands/agents.py` (79 lines) | `src/cli/agents.ts` | |
| `commands/lock.py` (102 lines) | `src/cli/lock.ts` | |
| `commands/telemetry_cmd.py` (76 lines) | `src/cli/telemetry.ts` | |
| _(new)_ | `src/cli/mcp.ts` | **New**: Start MCP server. `auto-skill mcp`. Imports and starts `src/mcp/server.ts` over stdio. (from qmd) |

### 6.3 — Slash commands (no change)

`commands/status.md`, `commands/review-patterns.md`, `commands/load-skill.md` are markdown files consumed by agents. No migration needed.

---

## 7. Web UI Migration

### 7.1 — Flask → Hono

```ts
// src/web/app.ts
import { Hono } from "hono";
import { serveStatic } from "hono/node-server/serve-static";

const app = new Hono();

app.get("/", serveStatic({ path: "./src/web/templates/index.html" }));

app.get("/api/skills", async (c) => {
  const skills = await suggester.suggestForContext(context);
  return c.json(skills);
});

app.get("/api/stats", async (c) => {
  const stats = tracker.getStats();
  return c.json(stats);
});

app.get("/api/graduation", async (c) => {
  const candidates = manager.getCandidates();
  return c.json(candidates);
});

export { app };
```

### 7.2 — Templates

The existing `web/templates/index.html` is mostly client-side JS with minimal Jinja2 templating. Replace the few `{{ variable }}` expressions with a simple string replace at serve time, or switch to fully client-side fetch from `/api/*` endpoints.

### 7.3 — Launch

Replace `start-web.sh` / `start-web.bat` with a package.json script:
```json
"scripts": {
  "web": "tsx src/web/app.ts"
}
```

Or add a CLI subcommand: `auto-skill web` → starts the dashboard.

---

## 8. Scripts Migration

| Python | TypeScript | Notes |
|--------|-----------|-------|
| `scripts/skill_registry.py` (80 lines) | `src/scripts/skill-registry.ts` | `yaml` package for frontmatter parsing. Now also inserts into `skill-store.ts` (content-addressable + FTS5 indexed). |
| `scripts/search_skills.py` (60 lines) | `src/scripts/search-skills.ts` | **Simplified**: delegates to `skill-store.searchSkills()` (FTS5 BM25). The naive JS tokenizer + scoring is replaced entirely. This module becomes a thin wrapper over the FTS5 query. |
| `scripts/get_skill.py` (60 lines) | `src/scripts/get-skill.ts` | File matching + content loading. Can also retrieve by content hash from `skill_content` table. |
| `scripts/discover_skill.py` (60 lines) | `src/scripts/discover-skill.ts` | Search + threshold checking. Uses FTS5 backend. |
| `scripts/list_skills.py` (40 lines) | `src/scripts/list-skills.ts` | Index + summary output. Queries `skills` table grouped by collection. |

These modules are significantly simplified by the FTS5-backed skill store — the search and indexing logic moves into SQLite.

---

## 9. Test Suite Migration

### 9.1 — Framework: pytest → Vitest

| pytest concept | Vitest equivalent |
|----------------|-------------------|
| `def test_foo():` | `test("foo", () => { ... })` |
| `assert x == y` | `expect(x).toBe(y)` |
| `@pytest.fixture` | `beforeEach` / `afterEach` / factory functions |
| `tmp_path` fixture | `fs.mkdtempSync(path.join(os.tmpdir(), "test-"))` |
| `unittest.mock.patch` | `vi.mock()`, `vi.spyOn()`, `vi.fn()` |
| `@pytest.mark.slow` | `test.skip` / conditional or `describe.skip` |
| `conftest.py` | `vitest.setup.ts` or shared test utilities |

### 9.2 — Test files (1:1 port)

All 17 test files migrated:

| Python test | TypeScript test |
|-------------|----------------|
| `tests/test_event_store.py` | `tests/event-store.test.ts` |
| `tests/test_pattern_detector.py` | `tests/pattern-detector.test.ts` |
| `tests/test_skill_generator.py` | `tests/skill-generator.test.ts` |
| `tests/test_agent_registry.py` | `tests/agent-registry.test.ts` |
| `tests/test_lock_file.py` | `tests/lock-file.test.ts` |
| `tests/test_migrations.py` | `tests/migrations.test.ts` |
| `tests/test_path_security.py` | `tests/path-security.test.ts` |
| `tests/test_providers.py` | `tests/providers.test.ts` |
| `tests/test_multi_agent_output.py` | `tests/multi-agent-output.test.ts` |
| `tests/test_edge_cases.py` | `tests/edge-cases.test.ts` |
| `tests/test_v2_integration.py` | `tests/v2-integration.test.ts` |
| `tests/test_phase3_integration.py` | `tests/phase3-integration.test.ts` |
| `tests/test_performance.py` | `tests/performance.test.ts` |
| `tests/test_spec_compliance.py` | `tests/spec-compliance.test.ts` |
| `tests/test_telemetry.py` | `tests/telemetry.test.ts` |
| `tests/test_sequence_matcher.py` | `tests/sequence-matcher.test.ts` |
| `tests/test_wellknown_provider.py` | `tests/wellknown-provider.test.ts` |

### 9.3 — SQLite in tests

Use in-memory `better-sqlite3` databases (`:memory:`) for isolation. Same pattern as current Python tests.

---

## 10. Dependency Map

### Python → Node Replacements

| Python Package | Node Replacement | Notes |
|---------------|-----------------|-------|
| `PyYAML` | `yaml` | YAML parse/stringify |
| `sqlite3` (stdlib) | `better-sqlite3` | Sync API, native addon |
| `flask` | `hono` | Lightweight HTTP |
| `pygls` | `vscode-languageserver-protocol` | LSP types only |
| `tree-sitter` + grammars | `web-tree-sitter` + WASM grammars | Cross-platform, no native compile |
| `numpy` | **Drop** (or `ml-matrix` if needed) | Light usage — replace with plain JS math |
| `scikit-learn` | **Drop** (or `ml-classify-text`) | Light usage — replace with simple scoring |
| `requests` (implied) | Native `fetch()` | Built into Node 18+ |
| `subprocess` | `node:child_process` | `execSync` / `spawn` |
| `dataclasses` | TypeScript interfaces + Zod | Zod for runtime validation at boundaries |
| `argparse` | `commander` | CLI parsing |
| `hashlib` | `node:crypto` | SHA-256, etc. |
| `pathlib` / `os.path` | `node:path` + `node:fs` | |
| `re` | Native `RegExp` | |
| `datetime` | `Date` (or `dayjs` if formatting needed) | |
| `unittest.mock` | Vitest built-in mocks | `vi.mock()`, `vi.fn()`, `vi.spyOn()` |

### New Node Dependencies

**Runtime** (keep minimal — babysitter ships with only 3 runtime deps):

| Package | Purpose | Size | Source |
|---------|---------|------|--------|
| `commander` | CLI framework | ~50KB | babysitter pattern |
| `yaml` | YAML parsing | ~100KB | qmd uses same |
| `better-sqlite3` | SQLite driver (FTS5 included) | Native addon | qmd validates SQLite+FTS5 stack |
| `ulid` | Sortable unique IDs | ~3KB | babysitter pattern |
| `zod` | Runtime validation | ~50KB | qmd uses same |
| `@modelcontextprotocol/sdk` | MCP server protocol | ~200KB | from qmd's MCP architecture |
| `hono` | Web server (optional, for dashboard) | ~14KB | |

**Optional (advanced features):**

| Package | Purpose | Source |
|---------|---------|--------|
| `sqlite-vec` | Vector similarity search for skills | from qmd — sqlite-vec extension |
| `web-tree-sitter` | Code structure analysis (LSP analyzer) | |
| `vscode-languageserver-protocol` | LSP types | |

Note: `sqlite-vec` is optional. FTS5 is built into SQLite and works without any extension. Vector search is an upgrade path for semantic skill matching.

**Dev-only:**

| Package | Purpose |
|---------|---------|
| `typescript` | Type checking + compilation |
| `vitest` | Test runner |
| `eslint` | Linting |
| `@typescript-eslint/parser` | TS-aware lint rules |
| `@typescript-eslint/eslint-plugin` | TS lint rules |
| `tsx` | Dev-time TS execution |
| `rimraf` | Clean build artifacts |
| `@types/better-sqlite3` | Type definitions |

---

## 11. Distribution Changes

### 11.1 — npm (primary — massively simplified)

**Before**: `npx skills add MaTriXy/auto-skill` → runs `postinstall` bash script → detects Python → prompts user → installs PyPI package via pip/uv.

**After**: `npx skills add MaTriXy/auto-skill` → just works. It's already Node.

Also available as:
- `npm install -g auto-skill` → global CLI
- `npx auto-skill` → one-off execution

The `"bin"` field in package.json handles the `auto-skill` command automatically.

### 11.2 — PyPI (removed)

- Delete `pyproject.toml`, `requirements.txt`, `PYPI_PUBLISHING.md`
- Publish a final v3.x release to PyPI with deprecation notice pointing to npm
- Remove all pip/uv install instructions from docs

### 11.3 — postinstall (removed)

- Delete `install-cli.sh` and `skills/install-cli.sh`
- Remove `"postinstall": "bash install-cli.sh || true"` from package.json
- No postinstall needed — the package is already Node

### 11.4 — Plugin manifest

Update `.claude-plugin/plugin.json` hook commands: `python3` → `node`.

---

## 12. CI/CD

### 12.1 — GitHub Actions: Test workflow

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-13, windows-2022]
        node-version: [18, 20, 22]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm run typecheck
      - run: npm run lint
      - run: npm test
      - run: npm run build
```

**3 OS x 3 Node versions = 9 environments** (babysitter does 3x2=6; we add Node 22).

### 12.2 — GitHub Actions: Release workflow

```yaml
name: Release
on:
  push:
    tags: ["v*"]
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          registry-url: "https://registry.npmjs.org"
      - run: npm ci
      - run: npm run build
      - run: npm test
      - run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### 12.3 — Docusaurus workflow (unchanged)

The existing `.github/workflows/docs.yml` is already Node-based. Only content updates needed.

---

## 13. Bun Compatibility

The project targets Node 18+ as primary runtime but should work on Bun. qmd is Bun-native and validates that the SQLite + FTS5 stack works well on Bun — our abstraction layer ensures both runtimes are supported.

| Area | Node | Bun | Strategy |
|------|------|-----|----------|
| **SQLite** | `better-sqlite3` (native addon, FTS5 built-in) | `bun:sqlite` (built-in, FTS5 built-in) | Abstract via `src/core/db.ts`. Both drivers support FTS5 natively. |
| **sqlite-vec** | Loaded via `db.loadExtension()` | Loaded via `db.loadExtension()` | Same API on both. qmd uses this on Bun; `better-sqlite3` supports it on Node. |
| **Fetch** | `global.fetch` (Node 18+) | `global.fetch` (built-in) | Same API. No wrapper needed. |
| **FS** | `node:fs` | Bun-compatible | Bun implements Node's fs API. |
| **Crypto** | `node:crypto` | Bun-compatible | Same. |
| **child_process** | `node:child_process` | Bun-compatible | Same. |
| **MCP server** | `@modelcontextprotocol/sdk` (stdio transport) | Same (Bun supports stdio) | qmd runs MCP on Bun. Same SDK works on Node. |
| **Build** | `tsc` | `tsc` (or `bun build` optional) | Keep `tsc` as canonical build. Note: qmd found that `bun build --compile` breaks sqlite-vec — avoid compiled binaries if using vector search. |
| **Test** | `vitest` | `bun test` (optional) | Keep vitest as canonical. Bun can run vitest too. |

### SQLite abstraction layer

```ts
// src/core/db.ts
import type Database from "better-sqlite3";

export function openDatabase(dbPath: string): Database.Database {
  let db: Database.Database;

  // @ts-ignore — Bun global detection
  if (typeof Bun !== "undefined") {
    // Bun has built-in SQLite (same sync API as better-sqlite3)
    // qmd validates this path works with FTS5 + sqlite-vec
    const { Database: BunDB } = require("bun:sqlite");
    db = new BunDB(dbPath);
  } else {
    const BetterSqlite3 = require("better-sqlite3");
    db = new BetterSqlite3(dbPath);
  }

  // qmd-style connection setup
  db.pragma("journal_mode = WAL");
  db.pragma("foreign_keys = ON");

  // Optional: load sqlite-vec for vector search
  try {
    const vecPath = require("sqlite-vec").getLoadablePath();
    db.loadExtension(vecPath);
  } catch {
    // sqlite-vec not installed — FTS5 still works, vector search disabled
  }

  return db;
}
```

---

## 14. FTS5 Skill Store & Content-Addressable Storage

> Adopted from `MaTriXy/qmd`'s `store.ts` — the core pattern of content-addressable storage with FTS5 full-text search and auto-sync triggers.

### 14.1 — Schema

The skill store uses three tables plus an FTS5 virtual table with auto-sync triggers. This replaces the naive in-memory keyword search from `scripts/search_skills.py`.

```sql
-- Content-addressable skill storage (from qmd's content table)
-- Skills stored by SHA-256 hash — enables deduplication and integrity verification
CREATE TABLE IF NOT EXISTS skill_content (
  hash TEXT PRIMARY KEY,                         -- SHA-256 of body
  body TEXT NOT NULL,                            -- Full SKILL.md content
  frontmatter TEXT,                              -- Parsed YAML frontmatter as JSON
  created_at TEXT DEFAULT (datetime('now'))
);

-- Skill metadata referencing content by hash (from qmd's documents table)
CREATE TABLE IF NOT EXISTS skills (
  id TEXT PRIMARY KEY,                           -- ULID
  name TEXT NOT NULL,                            -- Skill name (kebab-case)
  collection TEXT NOT NULL DEFAULT 'auto',       -- 'auto' | 'local' | 'external' | 'graduated'
  filepath TEXT,                                 -- Source file path (if file-based)
  hash TEXT REFERENCES skill_content(hash),      -- Content hash (FK)
  description TEXT,                              -- Short description
  tags TEXT,                                     -- JSON array of tags
  confidence REAL DEFAULT 0.5,                   -- Confidence score (0.0–1.0)
  agent_type TEXT,                               -- Source agent type
  active INTEGER DEFAULT 1,                      -- Soft delete flag
  source_url TEXT,                               -- External URL (for external/skillssh skills)
  author TEXT,                                   -- Skill author
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_skills_collection ON skills(collection);
CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(name);
CREATE INDEX IF NOT EXISTS idx_skills_hash ON skills(hash);
CREATE INDEX IF NOT EXISTS idx_skills_active ON skills(active);

-- FTS5 full-text index (from qmd's documents_fts pattern)
-- Uses unicode61 tokenizer for proper Unicode handling
CREATE VIRTUAL TABLE IF NOT EXISTS skills_fts USING fts5(
  name,
  description,
  body,
  tags,
  content='skills',
  content_rowid='rowid',
  tokenize='unicode61'
);

-- Auto-sync triggers (from qmd's documents_ai/ad/au pattern)
-- These keep the FTS index in sync with the skills table automatically.
-- No manual FTS updates needed — INSERT/UPDATE/DELETE on skills table triggers FTS sync.

CREATE TRIGGER IF NOT EXISTS skills_ai AFTER INSERT ON skills BEGIN
  INSERT INTO skills_fts(rowid, name, description, body, tags)
  SELECT new.rowid, new.name, new.description, sc.body, new.tags
  FROM skill_content sc WHERE sc.hash = new.hash;
END;

CREATE TRIGGER IF NOT EXISTS skills_ad AFTER DELETE ON skills BEGIN
  INSERT INTO skills_fts(skills_fts, rowid, name, description, body, tags)
  VALUES('delete', old.rowid, old.name, old.description,
    (SELECT body FROM skill_content WHERE hash = old.hash), old.tags);
END;

CREATE TRIGGER IF NOT EXISTS skills_au AFTER UPDATE ON skills BEGIN
  INSERT INTO skills_fts(skills_fts, rowid, name, description, body, tags)
  VALUES('delete', old.rowid, old.name, old.description,
    (SELECT body FROM skill_content WHERE hash = old.hash), old.tags);
  INSERT INTO skills_fts(rowid, name, description, body, tags)
  SELECT new.rowid, new.name, new.description, sc.body, new.tags
  FROM skill_content sc WHERE sc.hash = new.hash;
END;
```

### 14.2 — Skill Store API (`src/core/skill-store.ts`)

Factory pattern matching qmd's `createStore()`:

```ts
export interface SkillStore {
  // Content-addressable storage
  insertContent(body: string, frontmatter?: Record<string, unknown>): string; // returns hash
  getContent(hash: string): SkillContent | undefined;

  // Skill CRUD
  insertSkill(skill: NewSkill): string; // returns ULID
  updateSkill(id: string, updates: Partial<SkillMetadata>): void;
  deactivateSkill(id: string): void;
  getSkill(nameOrId: string): SkillResult | undefined;
  getSkillByHash(hash: string): SkillResult | undefined;
  listSkills(collection?: string): SkillResult[];

  // FTS5 search (replaces scripts/search_skills.py entirely)
  searchSkills(query: string, opts?: SearchOptions): SearchResult[];

  // Collection management (from qmd's collection model)
  getCollectionStats(): CollectionInfo[];

  // Maintenance
  vacuumDatabase(): void;
  cleanupOrphanedContent(): number; // returns count removed
}

export interface SearchOptions {
  collection?: string;     // filter by collection
  limit?: number;          // max results (default 10)
  minScore?: number;       // BM25 score threshold
  activeOnly?: boolean;    // default true
}

export interface SearchResult extends SkillResult {
  score: number;           // BM25 relevance score
}

export function createSkillStore(dbPath?: string): SkillStore {
  const db = openDatabase(dbPath ?? getDefaultDbPath());
  initializeSchema(db);
  return bindMethods(db);
}
```

### 14.3 — FTS5 Search Implementation

```ts
function searchSkills(db: Database, query: string, opts: SearchOptions = {}): SearchResult[] {
  const { collection, limit = 10, minScore, activeOnly = true } = opts;

  // Sanitize query for FTS5 syntax (from qmd's sanitizeFTSQuery pattern)
  const sanitized = sanitizeFTSQuery(query);

  let sql = `
    SELECT s.*, sc.body, sc.frontmatter, bm25(skills_fts) as score
    FROM skills_fts fts
    JOIN skills s ON s.rowid = fts.rowid
    JOIN skill_content sc ON sc.hash = s.hash
    WHERE skills_fts MATCH ?
  `;
  const params: unknown[] = [sanitized];

  if (activeOnly) {
    sql += " AND s.active = 1";
  }
  if (collection) {
    sql += " AND s.collection = ?";
    params.push(collection);
  }
  if (minScore !== undefined) {
    sql += " AND bm25(skills_fts) <= ?"; // BM25 scores are negative; lower = better
    params.push(minScore);
  }

  sql += " ORDER BY bm25(skills_fts) LIMIT ?";
  params.push(limit);

  return db.prepare(sql).all(...params) as SearchResult[];
}

// FTS5 query sanitizer (from qmd's store.ts)
// Strips special FTS5 operators that could cause syntax errors
function sanitizeFTSQuery(query: string): string {
  return query
    .replace(/[*"():^{}[\]~`|\\]/g, " ")  // Remove FTS5 special chars
    .replace(/\b(AND|OR|NOT|NEAR)\b/gi, '"$1"')  // Quote reserved words
    .replace(/\s+/g, " ")
    .trim();
}
```

### 14.4 — Optional: Vector Search with sqlite-vec

When `sqlite-vec` is available, semantic search can be added as a second search path. This mirrors qmd's two-tier search (BM25 + vector) without the heavy LLM parts.

```sql
-- Vector embedding storage (from qmd's content_vectors + vectors_vec pattern)
-- Only created if sqlite-vec extension is loaded
CREATE TABLE IF NOT EXISTS skill_vectors (
  hash TEXT NOT NULL,                    -- References skill_content.hash
  seq INTEGER NOT NULL DEFAULT 0,        -- Chunk sequence (0 for whole-doc)
  model TEXT NOT NULL,                   -- Embedding model identifier
  embedded_at TEXT DEFAULT (datetime('now')),
  PRIMARY KEY (hash, seq)
);

-- Virtual vector index (cosine similarity search)
CREATE VIRTUAL TABLE IF NOT EXISTS skill_vectors_vec USING vec0(
  hash_seq TEXT PRIMARY KEY,             -- "{hash}:{seq}" composite key
  embedding float[384]                   -- Embedding dimensions (model-dependent)
);
```

Vector search implementation (optional, same two-step approach as qmd to avoid join hangs):
```ts
function searchSkillsVector(db: Database, queryEmbedding: number[], limit = 10): SearchResult[] {
  // Step 1: Get vector candidates (qmd's two-step pattern)
  const candidates = db.prepare(`
    SELECT hash_seq, distance
    FROM skill_vectors_vec
    WHERE embedding MATCH ?
    ORDER BY distance
    LIMIT ?
  `).all(JSON.stringify(queryEmbedding), limit * 2);

  // Step 2: Join with skill metadata
  const hashes = candidates.map(c => c.hash_seq.split(":")[0]);
  // ... join with skills table for full results
}
```

This is entirely optional and gated behind `sqlite-vec` availability. FTS5 is the baseline.

### 14.5 — Content Hashing (from qmd)

```ts
import { createHash } from "node:crypto";

export function hashContent(body: string): string {
  return createHash("sha256").update(body, "utf8").digest("hex");
}

// Insert skill content with deduplication
function insertContent(db: Database, body: string, frontmatter?: Record<string, unknown>): string {
  const hash = hashContent(body);
  db.prepare(`
    INSERT OR IGNORE INTO skill_content (hash, body, frontmatter)
    VALUES (?, ?, ?)
  `).run(hash, body, frontmatter ? JSON.stringify(frontmatter) : null);
  return hash;
}
```

### 14.6 — Multi-Format Output (`src/formatter/index.ts`)

Adopted from qmd's `formatter.ts` — the CLI and API support multiple output formats:

```ts
export type OutputFormat = "json" | "csv" | "md" | "cli";

export function formatSearchResults(
  results: SearchResult[],
  format: OutputFormat = "cli"
): string {
  switch (format) {
    case "json": return JSON.stringify(results, null, 2);
    case "csv":  return formatCSV(results);
    case "md":   return formatMarkdown(results);
    case "cli":  return formatCLI(results);
  }
}
```

Used by `auto-skill search`, `auto-skill discover`, and the `/api/skills` endpoint.

---

## 15. MCP Server

> Adopted from `MaTriXy/qmd`'s `mcp.ts` — expose auto-skill as an MCP server so any MCP-compatible agent can search and retrieve skills.

### 15.1 — Architecture

The MCP server runs over stdio (same as qmd) and exposes skill search, retrieval, and system status as tools. This makes auto-skill's skill database accessible to Claude Desktop, Claude Code, and any other MCP client.

```
auto-skill mcp   →  starts MCP server on stdio
                     ├── tool: search_skills
                     ├── tool: get_skill
                     ├── tool: list_skills
                     ├── tool: pattern_stats
                     ├── resource: skill://{collection}/{name}
                     └── prompt: skill_search (search guidance)
```

### 15.2 — Implementation (`src/mcp/server.ts`)

```ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { createSkillStore } from "../core/skill-store.js";

export function createMcpServer() {
  const server = new McpServer({
    name: "auto-skill",
    version: "4.0.0",
  });
  const store = createSkillStore();

  // Tool: Full-text search over all indexed skills
  server.tool(
    "search_skills",
    "Search for skills using BM25 full-text search",
    {
      query: z.string().describe("Search query"),
      collection: z.string().optional().describe("Filter by collection: auto, local, external, graduated"),
      limit: z.number().optional().describe("Max results (default 10)"),
      format: z.enum(["json", "md"]).optional().describe("Output format"),
    },
    async ({ query, collection, limit, format }) => {
      const results = store.searchSkills(query, { collection, limit: limit ?? 10 });
      const text = format === "md"
        ? formatMarkdown(results)
        : JSON.stringify(results, null, 2);
      return { content: [{ type: "text", text }] };
    }
  );

  // Tool: Get a specific skill by name or ID
  server.tool(
    "get_skill",
    "Retrieve a specific skill's full content",
    {
      name: z.string().describe("Skill name or ULID"),
    },
    async ({ name }) => {
      const skill = store.getSkill(name);
      if (!skill) return { content: [{ type: "text", text: `Skill not found: ${name}` }] };
      return { content: [{ type: "text", text: skill.body }] };
    }
  );

  // Tool: List all skills grouped by collection
  server.tool(
    "list_skills",
    "List all available skills with metadata",
    {
      collection: z.string().optional().describe("Filter by collection"),
    },
    async ({ collection }) => {
      const skills = store.listSkills(collection);
      return { content: [{ type: "text", text: JSON.stringify(skills, null, 2) }] };
    }
  );

  // Tool: Pattern detection statistics
  server.tool(
    "pattern_stats",
    "Show pattern detection and skill adoption statistics",
    {},
    async () => {
      const stats = store.getCollectionStats();
      return { content: [{ type: "text", text: JSON.stringify(stats, null, 2) }] };
    }
  );

  // Resource: skill:// virtual paths (from qmd's qmd:// pattern)
  server.resource(
    "skill://{collection}/{name}",
    "Access a skill by virtual path",
    async (uri) => {
      const [collection, name] = uri.path.split("/").filter(Boolean);
      const skill = store.getSkill(name);
      if (!skill) return { contents: [] };
      return {
        contents: [{
          uri: uri.href,
          mimeType: "text/markdown",
          text: skill.body,
        }],
      };
    }
  );

  // Prompt: Help agents use skill search effectively
  server.prompt(
    "skill_search",
    "Guide for searching the auto-skill database",
    async () => ({
      messages: [{
        role: "user",
        content: {
          type: "text",
          text: `You have access to the auto-skill database via MCP tools.

Use search_skills for keyword search (e.g., "error handling", "TDD workflow").
Use get_skill to retrieve the full content of a specific skill.
Use list_skills to browse available skills by collection.

Collections: auto (auto-detected), local (user-created), external (from skills.sh), graduated (promoted from external).`
        }
      }]
    })
  );

  return server;
}
```

### 15.3 — CLI Integration

Add `mcp` subcommand to the CLI:

```ts
// In src/cli/cli.ts
program
  .command("mcp")
  .description("Start MCP server (for Claude Desktop, Claude Code, etc.)")
  .action(async () => {
    const { createMcpServer } = await import("../mcp/server.js");
    const { StdioServerTransport } = await import("@modelcontextprotocol/sdk/server/stdio.js");
    const server = createMcpServer();
    const transport = new StdioServerTransport();
    await server.connect(transport);
  });
```

### 15.4 — Claude Desktop / Claude Code Configuration

Users can add auto-skill as an MCP server:

```jsonc
// Claude Desktop: ~/Library/Application Support/Claude/claude_desktop_config.json
// Claude Code: .claude/mcp_servers.json
{
  "mcpServers": {
    "auto-skill": {
      "command": "auto-skill",
      "args": ["mcp"]
    }
  }
}
```

### 15.5 — Testing

```ts
// tests/mcp-server.test.ts
import { createMcpServer } from "../src/mcp/server.js";

test("search_skills returns BM25-ranked results", async () => {
  // Set up in-memory skill store with test data
  // Call tool directly via MCP server
  // Assert results are ranked and formatted correctly
});

test("get_skill returns full content", async () => {
  // Insert skill, retrieve by name, verify body matches
});

test("resource URI resolves to skill content", async () => {
  // Test skill://auto/my-skill resolution
});
```

---

## 16. Cleanup & Removal

### Files to DELETE

```
# All Python source
core/*.py
core/providers/*.py
commands/*.py (NOT commands/*.md)
hooks/observer.py
scripts/*.py
web/app.py
examples/*.py

# All __init__.py
core/__init__.py
core/providers/__init__.py
commands/__init__.py
hooks/__init__.py
scripts/__init__.py
tests/__init__.py

# Python config & packaging
pyproject.toml
requirements.txt
web/requirements.txt
PYPI_PUBLISHING.md

# Python install scripts
install-cli.sh
skills/install-cli.sh
start-web.sh
start-web.bat
web/start-web.sh

# Python test files (replaced by .test.ts)
tests/test_*.py
```

### Files to UPDATE

| File | Changes |
|------|---------|
| `README.md` | Remove all Python/pip references. Update install to npm only. Update dev instructions. |
| `CLAUDE.md` | Update architecture, file structure, dev commands, dependency info. |
| `CHANGELOG.md` | Add v4.0.0 entry documenting the Node migration. |
| `package.json` | Full rewrite (see Section 2.1). |
| `hooks/hooks.json` | `python3` → `node` (see Section 5.2). |
| `.claude-plugin/plugin.json` | Update hook commands. |
| `.gitignore` | Remove Python patterns (*.pyc, __pycache__, .egg-info, etc). Add `dist/`, `node_modules/`, `*.tsbuildinfo`. |
| `.github/workflows/*` | Python CI → Node CI (see Section 12). |

### Files UNCHANGED

| File | Reason |
|------|--------|
| `skills/*.md` | Agent-consumable markdown. No code. |
| `commands/*.md` | Slash commands. Markdown only. |
| `website/` | Already Node-based Docusaurus. Content updates only. |
| `references/registry.json` | Build artifact. Format unchanged. |
| `LICENSE` | Unchanged. |

---

## 17. Execution Order

Recommended sequence for implementation. Each phase should be independently committable and testable.

| Phase | What | Files | Est. Scope | Source |
|-------|------|-------|------------|--------|
| **1** | Scaffold | package.json, tsconfig.json, vitest.config.ts, eslint config, bin/auto-skill.js, .gitignore, directory structure | New files only | babysitter |
| **2** | Types + utilities | `src/types/index.ts`, `src/util/atomic-write.ts`, `src/util/ulid.ts`, `src/util/fs.ts`, `src/util/fts.ts` | ~350 lines | babysitter + qmd |
| **3** | Layer 0: pure logic | path-security, config, spec-validator | ~400 lines | |
| **4** | Layer 1: storage | **db.ts** (qmd-style factory), event-store, **skill-store.ts** (FTS5 + content-addressable), migrations (incl. FTS5 triggers), lock-file, skill-tracker | ~1200 lines | **qmd** |
| **5** | Layer 2: analysis | sequence-matcher, session-analyzer, design-pattern-detector, lsp-analyzer, pattern-detector | ~500 lines | |
| **6** | Layer 3: generation | skill-generator, graduation-manager, agent-registry, telemetry | ~400 lines | |
| **7** | Layer 4: discovery | providers, skillssh-client/publisher, mental-analyzer, unified-suggester (now FTS5-backed) | ~600 lines | **qmd** (search) |
| **8** | Hooks | observer.ts + hooks.json update | ~200 lines | babysitter (graceful degradation) |
| **9** | CLI | cli.ts factory + all commands (incl. `search`, `mcp`) | ~600 lines | babysitter (factory) |
| **10** | Formatter | `src/formatter/index.ts` — multi-format output (JSON, CSV, MD, CLI) | ~150 lines | **qmd** |
| **11** | MCP Server | `src/mcp/server.ts` — skill search, retrieval, stats as MCP tools | ~250 lines | **qmd** |
| **12** | Scripts | 5 utility scripts (simplified — search delegates to FTS5) | ~200 lines | **qmd** (simplified) |
| **13** | Web UI | Hono app + template | ~150 lines | |
| **14** | Tests | All 19 test files (17 ported + skill-store + mcp-server) | ~1800 lines | |
| **15** | CI/CD | GitHub Actions workflows (3 OS x 3 Node) | ~100 lines YAML | babysitter |
| **16** | Cleanup | Delete all Python files, update docs | Deletion + text edits | |
| **17** | Release | v4.0.0 tag, npm publish, PyPI deprecation notice | Process | |

**Key change from v1 plan**: Phases 4 (storage) and 7 (discovery) are significantly enhanced by qmd patterns. Phase 4 grows from ~800 to ~1200 lines due to the FTS5 skill store, triggers, and content-addressable storage. Phases 10 (formatter) and 11 (MCP server) are entirely new additions from qmd.

---

## 18. Risk Areas

| Risk | Impact | Mitigation | Source |
|------|--------|------------|--------|
| **`better-sqlite3` native compilation** | `node-gyp` can fail on some systems (missing build tools) | Provide fallback guidance in docs. Bun has built-in SQLite. Consider `sql.js` (WASM, zero native deps) as optional fallback. | babysitter |
| **FTS5 availability** | FTS5 must be compiled into SQLite | `better-sqlite3` bundles its own SQLite with FTS5 enabled by default. Bun's built-in SQLite also includes FTS5. qmd validates this works on both. **Low risk.** | qmd |
| **sqlite-vec extension loading** | `loadExtension()` may fail on some platforms or restricted environments | sqlite-vec is optional — the system degrades gracefully to FTS5-only search. qmd found that `bun build --compile` breaks extension loading; avoid compiled binaries. | qmd |
| **`@modelcontextprotocol/sdk` stability** | MCP SDK is pre-1.0, API may change | Pin to specific version. MCP server is an additive feature — the system works without it. qmd uses the same SDK successfully. | qmd |
| **`numpy`/`scikit-learn` replacement** | ML-based scoring might lose accuracy | Current usage is light (cosine similarity, basic classification). Replace with plain JS implementations. With FTS5 BM25 replacing keyword scoring, the ML path is less critical. | |
| **`tree-sitter` WASM performance** | WASM is slower than native bindings | LSP analyzer is optional/advanced. Start with WASM, benchmark. Native `tree-sitter` npm bindings exist as upgrade path. | |
| **ESM-only dependencies** | Some npm packages are ESM-only, CJS project can't `require()` them | Check all deps upfront. `@modelcontextprotocol/sdk` is ESM — use dynamic `import()` for it (as shown in CLI mcp command). Most other deps support CJS. | |
| **Breaking change for PyPI users** | `pip install aiskill` users lose their install path | Publish final Python v3.x with deprecation warning. Point to npm in README. Major version bump (v4.0.0). | |
| **Hook cold-start latency** | Node startup is ~50ms, could add overhead on every tool call | Actually a **win** — Python cold-start is ~100ms. Bun is ~5ms. | |
| **Windows path handling** | `node:path` has `path.win32` vs `path.posix` | Use `path.resolve()` and `path.join()` consistently. Test on Windows in CI (see matrix). | babysitter |
| **Database migration from Python → Node** | Existing SQLite databases created by Python version | Schema is the same. SQLite is cross-language. Existing `.db` files work with `better-sqlite3` without modification. New FTS5 tables are additive — old DBs get the new tables via migration. Storage layout version for future proofing. | qmd |
| **FTS5 trigger performance on bulk insert** | Auto-sync triggers fire on every INSERT/UPDATE/DELETE | For bulk skill import, wrap in a transaction (SQLite batches trigger execution). qmd handles this fine for hundreds of documents. | qmd |
