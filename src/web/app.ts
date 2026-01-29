/**
 * Web UI for Auto-Skill - Hono-based REST API and dashboard.
 *
 * Provides:
 * - Skill browser API (local + external)
 * - Adoption dashboard stats
 * - Graduation management
 * - Search across all providers
 */
import { Hono } from "hono";
import { cors } from "hono/cors";
import path from "node:path";
import os from "node:os";

const CONFIG = {
  skillsDir: path.join(os.homedir(), ".claude", "skills", "auto"),
  trackerDb: path.join(os.homedir(), ".claude", "auto-skill", "skill_tracker.db"),
  eventStoreDb: path.join(os.homedir(), ".claude", "auto-skill", "events.db"),
};

/**
 * Creates and configures the Hono application with all API routes
 * and the dashboard HTML page.
 */
export function createApp(): Hono {
  const app = new Hono();

  // Middleware
  app.use("*", cors());

  // Health check
  app.get("/api/health", (c) => c.json({ status: "ok", version: "4.0.0" }));

  // List all skills
  app.get("/api/skills", async (c) => {
    try {
      const { createLocalProvider } = await import("../core/providers/local-provider");
      const provider = createLocalProvider();
      const skills = await provider.search("", 100);
      return c.json({ success: true, count: skills.length, skills });
    } catch (err) {
      return c.json({ success: false, error: String(err) }, 500);
    }
  });

  // Get skill details
  app.get("/api/skills/:name", async (c) => {
    try {
      const name = c.req.param("name");
      const { createLocalProvider } = await import("../core/providers/local-provider");
      const provider = createLocalProvider();
      const skill = await provider.getSkillDetails(name);
      if (!skill) return c.json({ success: false, error: "Skill not found" }, 404);
      return c.json({ success: true, skill });
    } catch (err) {
      return c.json({ success: false, error: String(err) }, 500);
    }
  });

  // Dashboard stats
  app.get("/api/stats/dashboard", async (c) => {
    try {
      return c.json({
        success: true,
        stats: {
          overview: {
            total_skills: 0,
            local_skills: 0,
            external_skills: 0,
            total_usage: 0,
            avg_success_rate: 0,
          },
          graduation: { candidates: 0, graduated: 0 },
          top_skills: [],
        },
      });
    } catch (err) {
      return c.json({ success: false, error: String(err) }, 500);
    }
  });

  // Graduation candidates
  app.get("/api/graduation/candidates", async (c) => {
    try {
      return c.json({ success: true, count: 0, candidates: [] });
    } catch (err) {
      return c.json({ success: false, error: String(err) }, 500);
    }
  });

  // Graduate a skill
  app.post("/api/graduation/graduate", async (c) => {
    try {
      const body = await c.req.json();
      const skillName = body.skill_name;
      if (!skillName) {
        return c.json({ success: false, error: "skill_name required" }, 400);
      }
      return c.json({ success: false, error: "Not yet implemented" }, 501);
    } catch (err) {
      return c.json({ success: false, error: String(err) }, 500);
    }
  });

  // Detect publishable skills
  app.get("/api/publish/detect", async (c) => {
    try {
      return c.json({ success: true, count: 0, publishable: [] });
    } catch (err) {
      return c.json({ success: false, error: String(err) }, 500);
    }
  });

  // Publish a skill
  app.post("/api/publish/publish", async (c) => {
    try {
      const body = await c.req.json();
      const skillName = body.skill_name;
      if (!skillName) {
        return c.json({ success: false, error: "skill_name required" }, 400);
      }
      return c.json({ success: false, error: "Not yet implemented" }, 501);
    } catch (err) {
      return c.json({ success: false, error: String(err) }, 500);
    }
  });

  // Search skills
  app.get("/api/search", async (c) => {
    try {
      const query = c.req.query("q") || "";
      if (!query) {
        return c.json({ success: false, error: "Query required" }, 400);
      }

      const { createProviderManager } = await import("../core/providers/manager");
      const { createLocalProvider } = await import("../core/providers/local-provider");
      const manager = createProviderManager();
      manager.register(createLocalProvider());

      const results = await manager.searchAll(query, 20);
      return c.json({ success: true, query, count: results.length, results });
    } catch (err) {
      return c.json({ success: false, error: String(err) }, 500);
    }
  });

  // Index page (HTML)
  app.get("/", (c) => {
    return c.html(getIndexHtml());
  });

  return app;
}

/**
 * Returns the dashboard HTML page as a string.
 * Includes inline CSS and JavaScript for a self-contained single-page app
 * styled with a dark theme matching GitHub's design language.
 */
function getIndexHtml(): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Auto-Skill Dashboard</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; }
    .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
    header { border-bottom: 1px solid #21262d; padding: 16px 0; margin-bottom: 24px; }
    header h1 { font-size: 24px; color: #58a6ff; }
    header p { color: #8b949e; margin-top: 4px; }
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
    .stat-card { background: #161b22; border: 1px solid #21262d; border-radius: 6px; padding: 16px; }
    .stat-card h3 { font-size: 14px; color: #8b949e; margin-bottom: 8px; }
    .stat-card .value { font-size: 32px; font-weight: 600; color: #58a6ff; }
    .section { margin-bottom: 24px; }
    .section h2 { font-size: 18px; margin-bottom: 12px; color: #c9d1d9; }
    .skill-list { list-style: none; }
    .skill-item { background: #161b22; border: 1px solid #21262d; border-radius: 6px; padding: 12px 16px; margin-bottom: 8px; }
    .skill-item .name { font-weight: 600; color: #58a6ff; }
    .skill-item .desc { color: #8b949e; font-size: 14px; margin-top: 4px; }
    .skill-item .meta { font-size: 12px; color: #6e7681; margin-top: 4px; }
    .confidence-bar { display: inline-block; width: 100px; height: 8px; background: #21262d; border-radius: 4px; overflow: hidden; vertical-align: middle; }
    .confidence-fill { height: 100%; background: #3fb950; border-radius: 4px; }
    #loading { text-align: center; padding: 40px; color: #8b949e; }
    .search-box { width: 100%; padding: 8px 12px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #c9d1d9; font-size: 14px; margin-bottom: 16px; }
    .search-box:focus { outline: none; border-color: #58a6ff; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Auto-Skill Dashboard</h1>
      <p>Skill discovery, adoption tracking, and management</p>
    </header>

    <div class="stats-grid" id="stats">
      <div class="stat-card"><h3>Total Skills</h3><div class="value" id="total-skills">-</div></div>
      <div class="stat-card"><h3>Local Skills</h3><div class="value" id="local-skills">-</div></div>
      <div class="stat-card"><h3>External Skills</h3><div class="value" id="external-skills">-</div></div>
      <div class="stat-card"><h3>Avg Success Rate</h3><div class="value" id="success-rate">-</div></div>
    </div>

    <div class="section">
      <h2>Skills</h2>
      <input type="text" class="search-box" placeholder="Search skills..." id="search-input">
      <ul class="skill-list" id="skill-list">
        <li id="loading">Loading skills...</li>
      </ul>
    </div>
  </div>

  <script>
    async function loadDashboard() {
      try {
        const [statsRes, skillsRes] = await Promise.all([
          fetch('/api/stats/dashboard'),
          fetch('/api/skills')
        ]);
        const stats = await statsRes.json();
        const skills = await skillsRes.json();

        if (stats.success) {
          document.getElementById('total-skills').textContent = stats.stats.overview.total_skills;
          document.getElementById('local-skills').textContent = stats.stats.overview.local_skills;
          document.getElementById('external-skills').textContent = stats.stats.overview.external_skills;
          document.getElementById('success-rate').textContent = (stats.stats.overview.avg_success_rate * 100).toFixed(0) + '%';
        }

        if (skills.success) {
          renderSkills(skills.skills);
        }
      } catch (err) {
        document.getElementById('skill-list').innerHTML = '<li>Failed to load data</li>';
      }
    }

    function renderSkills(skills) {
      const list = document.getElementById('skill-list');
      if (!skills.length) {
        list.innerHTML = '<li class="skill-item"><div class="desc">No skills found. Run auto-skill discover to get started.</div></li>';
        return;
      }
      list.innerHTML = skills.map(s => \`
        <li class="skill-item">
          <div class="name">\${s.name}</div>
          <div class="desc">\${s.description || ''}</div>
          <div class="meta">
            Source: \${s.source || 'local'}
            \${s.confidence !== undefined ? ' | Confidence: <span class="confidence-bar"><span class="confidence-fill" style="width:' + (s.confidence * 100) + '%"></span></span> ' + (s.confidence * 100).toFixed(0) + '%' : ''}
            \${s.tags?.length ? ' | Tags: ' + s.tags.join(', ') : ''}
          </div>
        </li>
      \`).join('');
    }

    document.getElementById('search-input').addEventListener('input', async (e) => {
      const q = e.target.value.trim();
      if (q.length < 2) { loadDashboard(); return; }
      try {
        const res = await fetch('/api/search?q=' + encodeURIComponent(q));
        const data = await res.json();
        if (data.success) renderSkills(data.results);
      } catch {}
    });

    loadDashboard();
  </script>
</body>
</html>`;
}

export { CONFIG };
