# Auto-Skill: Python → Node/Bun Migration Plan

> **Version**: 1.0 — Final consolidated plan
> **Target release**: v4.0.0
> **Scope**: Full rewrite of ~50 Python files to TypeScript, shipping as a pure npm package

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
14. [Cleanup & Removal](#14-cleanup--removal)
15. [Execution Order](#15-execution-order)
16. [Risk Areas](#16-risk-areas)

---

## 1. Design Decisions

Key architectural decisions, informed by analysis of `a5c-ai/babysitter` and the existing codebase.

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
| **SQLite driver** | **`better-sqlite3`** | Synchronous API, fast, well-maintained. Used for event store and skill tracker (query-heavy). Non-DB files use atomic file writes. |
| **Linting** | **ESLint + `@typescript-eslint`** | Proven combo, type-aware linting. Babysitter validates this works well at scale. |
| **Testing** | **Vitest** | Fast, native ESM/CJS support, great DX, built-in mocking. Same choice as babysitter. |
| **Web framework** | **Hono** | Ultralight (~14KB), runs on Node and Bun. The dashboard is simple enough that a full framework like Express/Fastify is overkill. |

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
│   │   └── fs.ts               # Common filesystem helpers
│   ├── cli/
│   │   ├── cli.ts              # createCli() factory (from babysitter pattern)
│   │   ├── init.ts             # auto-skill init
│   │   ├── discover.ts         # auto-skill discover
│   │   ├── agents.ts           # auto-skill agents
│   │   ├── lock.ts             # auto-skill lock
│   │   └── telemetry.ts        # auto-skill telemetry
│   ├── core/
│   │   ├── config.ts           # Configuration management
│   │   ├── event-store.ts      # SQLite event persistence
│   │   ├── migrations.ts       # DB schema versioning
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
│   │   ├── unified-suggester.ts  # Hybrid skill discovery
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
│   ├── scripts/
│   │   ├── skill-registry.ts   # Skill indexing
│   │   ├── search-skills.ts    # Skill search + scoring
│   │   ├── get-skill.ts        # Load skill content
│   │   ├── discover-skill.ts   # Skill discovery
│   │   └── list-skills.ts      # List available skills
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
│   ├── pattern-detector.test.ts
│   ├── skill-generator.test.ts
│   ├── agent-registry.test.ts
│   ├── lock-file.test.ts
│   ├── migrations.test.ts
│   ├── path-security.test.ts
│   ├── providers.test.ts
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
| `core/event_store.py` (100+ lines) | `src/core/event-store.ts` | `better-sqlite3` synchronous API. Same schema: `tool_events` table with session_id, project_path, timestamp, tool_name indexes. Use ULID for event IDs. |
| `core/migrations.py` (501 lines) | `src/core/migrations.ts` | Same pattern: `schema_version` table, ordered migration functions. Consider also supporting sequential SQL files like babysitter's `001_init.sql` approach. |
| `core/lock_file.py` (60 lines) | `src/core/lock-file.ts` | `node:crypto` for SHA-256. Use atomic-write utility for lock file writes. |
| `core/skill_tracker.py` (60 lines) | `src/core/skill-tracker.ts` | Same `better-sqlite3` driver as event-store. Same schema. |

**Storage versioning**: Add a `STORAGE_LAYOUT_VERSION` constant (e.g., `"2026.01-v4"`) to all storage paths. This enables future format migrations (adopted from babysitter).

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
| `core/unified_suggester.py` (60 lines) | `src/core/unified-suggester.ts` | Aggregation logic. Direct port. |

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
      program.command("discover").description("Discover skills").action(discoverCommand);
      program.command("agents").description("Manage agents").action(agentsCommand);
      program.command("lock").description("Lock file management").action(lockCommand);
      program.command("telemetry").description("View telemetry").action(telemetryCommand);
      program.command("stats").description("Show statistics").action(statsCommand);
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
| `commands/agents.py` (79 lines) | `src/cli/agents.ts` | |
| `commands/lock.py` (102 lines) | `src/cli/lock.ts` | |
| `commands/telemetry_cmd.py` (76 lines) | `src/cli/telemetry.ts` | |

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
| `scripts/skill_registry.py` (80 lines) | `src/scripts/skill-registry.ts` | `yaml` package for frontmatter parsing |
| `scripts/search_skills.py` (60 lines) | `src/scripts/search-skills.ts` | Tokenization + scoring logic |
| `scripts/get_skill.py` (60 lines) | `src/scripts/get-skill.ts` | File matching + content loading |
| `scripts/discover_skill.py` (60 lines) | `src/scripts/discover-skill.ts` | Search + threshold checking |
| `scripts/list_skills.py` (40 lines) | `src/scripts/list-skills.ts` | Index + summary output |

These are utility modules called by other parts of the system. Straightforward ports.

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

| Package | Purpose | Size |
|---------|---------|------|
| `commander` | CLI framework | ~50KB |
| `yaml` | YAML parsing | ~100KB |
| `better-sqlite3` | SQLite driver | Native addon |
| `ulid` | Sortable unique IDs | ~3KB |
| `hono` | Web server (optional, for dashboard) | ~14KB |
| `zod` | Runtime validation | ~50KB |

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

**Optional (advanced features):**

| Package | Purpose |
|---------|---------|
| `web-tree-sitter` | Code structure analysis (LSP analyzer) |
| `vscode-languageserver-protocol` | LSP types |

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

The project targets Node 18+ as primary runtime but should work on Bun.

| Area | Node | Bun | Strategy |
|------|------|-----|----------|
| **SQLite** | `better-sqlite3` (native addon) | `bun:sqlite` (built-in) | Abstract via `src/core/db.ts` that checks `typeof Bun !== "undefined"` and picks the driver. Same sync API surface. |
| **Fetch** | `global.fetch` (Node 18+) | `global.fetch` (built-in) | Same API. No wrapper needed. |
| **FS** | `node:fs` | Bun-compatible | Bun implements Node's fs API. |
| **Crypto** | `node:crypto` | Bun-compatible | Same. |
| **child_process** | `node:child_process` | Bun-compatible | Same. |
| **Build** | `tsc` | `tsc` (or `bun build` optional) | Keep `tsc` as canonical build. Add optional `"build:bun": "bun build src/index.ts --outdir dist"` script. |
| **Test** | `vitest` | `bun test` (optional) | Keep vitest as canonical. Bun can run vitest too. |

### SQLite abstraction layer

```ts
// src/core/db.ts
import type Database from "better-sqlite3";

export function openDatabase(path: string): Database.Database {
  // @ts-ignore — Bun global detection
  if (typeof Bun !== "undefined") {
    // Use Bun's built-in SQLite (same sync API)
    const { Database: BunDB } = require("bun:sqlite");
    return new BunDB(path);
  }
  const BetterSqlite3 = require("better-sqlite3");
  return new BetterSqlite3(path);
}
```

---

## 14. Cleanup & Removal

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

## 15. Execution Order

Recommended sequence for implementation. Each phase should be independently committable and testable.

| Phase | What | Files | Est. Scope |
|-------|------|-------|------------|
| **1** | Scaffold | package.json, tsconfig.json, vitest.config.ts, eslint config, bin/auto-skill.js, .gitignore, directory structure | New files only |
| **2** | Types + utilities | `src/types/index.ts`, `src/util/atomic-write.ts`, `src/util/ulid.ts`, `src/util/fs.ts` | ~300 lines |
| **3** | Layer 0: pure logic | path-security, config, spec-validator | ~400 lines |
| **4** | Layer 1: storage | db abstraction, event-store, migrations, lock-file, skill-tracker | ~800 lines |
| **5** | Layer 2: analysis | sequence-matcher, session-analyzer, design-pattern-detector, lsp-analyzer, pattern-detector | ~500 lines |
| **6** | Layer 3: generation | skill-generator, graduation-manager, agent-registry, telemetry | ~400 lines |
| **7** | Layer 4: discovery | providers, skillssh-client/publisher, mental-analyzer, unified-suggester | ~600 lines |
| **8** | Hooks | observer.ts + hooks.json update | ~200 lines |
| **9** | CLI | cli.ts factory + all commands | ~500 lines |
| **10** | Scripts | 5 utility scripts | ~300 lines |
| **11** | Web UI | Hono app + template | ~150 lines |
| **12** | Tests | All 17 test files | ~1500 lines |
| **13** | CI/CD | GitHub Actions workflows | ~100 lines YAML |
| **14** | Cleanup | Delete all Python files, update docs | Deletion + text edits |
| **15** | Release | v4.0.0 tag, npm publish, PyPI deprecation notice | Process |

---

## 16. Risk Areas

| Risk | Impact | Mitigation |
|------|--------|------------|
| **`better-sqlite3` native compilation** | `node-gyp` can fail on some systems (missing build tools) | Provide fallback guidance in docs. Bun has built-in SQLite. Consider `sql.js` (WASM, zero native deps) as optional fallback. |
| **`numpy`/`scikit-learn` replacement** | ML-based scoring might lose accuracy | Current usage is light (cosine similarity, basic classification). Replace with plain JS implementations. Benchmark against Python output. |
| **`tree-sitter` WASM performance** | WASM is slower than native bindings | LSP analyzer is optional/advanced. Start with WASM, benchmark. Native `tree-sitter` npm bindings exist as upgrade path. |
| **ESM-only dependencies** | Some npm packages are ESM-only, CJS project can't `require()` them | Check all deps upfront. Use dynamic `import()` for any ESM-only deps. Most deps in our list support CJS. |
| **Breaking change for PyPI users** | `pip install aiskill` users lose their install path | Publish final Python v3.x with deprecation warning. Point to npm in README. Major version bump (v4.0.0). |
| **Hook cold-start latency** | Node startup is ~50ms, could add overhead on every tool call | Actually a **win** — Python cold-start is ~100ms. Bun is ~5ms. |
| **Windows path handling** | `node:path` has `path.win32` vs `path.posix` | Use `path.resolve()` and `path.join()` consistently. Test on Windows in CI (see matrix). |
| **Database migration from Python → Node** | Existing SQLite databases created by Python version | Schema is the same. SQLite is cross-language. Existing `.db` files work with `better-sqlite3` without modification. Add storage layout version for future proofing. |
