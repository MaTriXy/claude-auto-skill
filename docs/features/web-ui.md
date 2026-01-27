# Web UI

Beautiful visual interface for managing skills, tracking adoption, and one-click operations.

![Web UI Dashboard](../assets/screenshots/dashboard.png)

---

## Overview

The Web UI provides a complete visual interface for Claude Auto-Skill:

- **Skill Browser**: Grid view with search/filter
- **Dashboard**: Real-time stats and charts
- **Graduation**: One-click skill promotion
- **Publishing**: Community skill sharing

**Tech Stack**:

- Flask (Python backend)
- Vanilla JavaScript (no frameworks)
- Material Design inspired
- Responsive (mobile-friendly)

---

## Starting the Server

=== "Convenience Script (Easiest)"

    ```bash
    # macOS/Linux
    ./start-web.sh

    # Windows
    start-web.bat

    # Custom port
    ./start-web.sh 3000
    ```

    ✨ **Benefits**: One command, handles everything, auto-detects uv

=== "With uv (Recommended)"

    ```bash
    cd web
    uv sync
    uv run python app.py
    ```

    ⚡ **Benefits**: Faster installation, automatic venv management

=== "With pip"

    ```bash
    cd web
    pip install -r requirements.txt
    python app.py
    ```

Default address: [http://localhost:8000](http://localhost:8000)

**Note**: If port 8000 is in use, specify a different port with the script: `./start-web.sh 3000`

### Custom Port

```bash
python app.py --port 8080
```

### Production Mode

```bash
export FLASK_ENV=production
python app.py
```

---

## Dashboard Tab

![Dashboard](../assets/screenshots/dashboard.png)

### Overview Stats

**5 Key Metrics**:

1. **Total Skills**: All skills (local + external)
2. **Local Skills**: Generated from your patterns
3. **External Skills**: From skills.sh
4. **Total Usage**: Cumulative skill uses
5. **Success Rate**: Average across all skills

**Visual Design**:

- Gradient purple cards
- Large numbers for quick scanning
- Descriptive labels

### Skill Browser

**Features**:

- **Grid Layout**: Responsive cards (1-4 columns)
- **Search**: Real-time filtering
- **Sort Options**: Confidence, usage, name
- **Card Details**:
  - Skill name
  - Source badge (local/external/mental)
  - Usage count
  - Success rate
  - Animated confidence bar

**Interactions**:

- **Hover**: Card lifts with shadow
- **Click**: View full details (coming soon)
- **Search**: Filters as you type

---

## Graduation Tab

![Graduation Tab](../assets/screenshots/graduation.png)

### Candidate Detection

**Criteria** (displayed at top):

```yaml
Confidence: ≥ 85%
Usage: ≥ 5 times
Success Rate: ≥ 80%
```

**Candidate Cards**:

- Skill name with graduation emoji 🎓
- Current stats (confidence, usage, success)
- Source indicator
- **Graduate to Local** button

### Graduation Process

1. **Detect**: Automatically finds eligible skills
2. **Review**: User sees candidate details
3. **Graduate**: Click button → instant promotion
4. **Update**: Dashboard refreshes with new local skill

**Post-Graduation**:

- Skill moved to local (80% confidence)
- Original metadata preserved
- Graduation history tracked
- Dashboard updated

---

## Publishing Tab

![Publishing Tab](../assets/screenshots/publishing.png)

### Publishable Detection

**Quality Criteria**:

- ✅ Has YAML frontmatter
- ✅ Has description section
- ✅ Has usage section
- ✅ Minimum 500 characters

**Publishable Cards**:

- Skill name with package emoji 📦
- "Ready to publish" indicator
- **Publish to skills.sh** button

### Publishing Process

1. **Detect**: Finds skills meeting criteria
2. **Review**: User confirms publication
3. **Publish**: Uploads to skills.sh (simulated)
4. **Track**: Records publication status

**Post-Publication**:

- Skill marked as published
- External URL tracked
- Community stats synced
- Install count monitored

---

## API Endpoints

The Web UI uses these REST endpoints:

### Skills

```http
GET /api/skills
```

Returns all skills with stats.

**Response**:

```json
{
  "success": true,
  "count": 42,
  "skills": [
    {
      "name": "tdd-workflow",
      "confidence": 0.85,
      "source": "local",
      "usage_count": 12,
      "success_rate": 0.92
    }
  ]
}
```

### Skill Detail

```http
GET /api/skills/<skill_name>
```

Returns detailed info for a skill.

### Dashboard Stats

```http
GET /api/stats/dashboard
```

Returns complete dashboard statistics.

### Graduation

```http
GET /api/graduation/candidates
POST /api/graduation/graduate
```

**Graduate Request**:

```json
{
  "skill_name": "stripe-integration"
}
```

**Graduate Response**:

```json
{
  "success": true,
  "skill_path": "~/.claude/skills/auto/stripe-integration.md"
}
```

### Publishing

```http
GET /api/publish/detect
POST /api/publish/publish
```

**Publish Request**:

```json
{
  "skill_name": "tdd-workflow"
}
```

**Publish Response**:

```json
{
  "success": true,
  "url": "https://skills.sh/skill/tdd-workflow"
}
```

### Search

```http
GET /api/search?q=<query>
```

Searches both local and external skills.

---

## Customization

### Colors

Edit `web/templates/index.html`:

```css
/* Change primary color */
.stat-card {
  background: linear-gradient(135deg, #your-color-1, #your-color-2);
}

/* Change accent */
.tab.active {
  color: #your-accent;
  border-bottom-color: #your-accent;
}
```

### Layout

**Card Grid**:

```css
.skills-grid {
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  /* Change 300px to adjust card size */
}
```

**Stats Cards**:

```css
.stats-grid {
  grid-template-columns: repeat(5, 1fr);
  /* Change 5 to adjust number of cards */
}
```

### Adding Features

**New Tab**:

1. Add tab button in HTML:
   ```html
   <button class="tab" data-tab="my-tab">My Tab</button>
   ```

2. Add tab content:
   ```html
   <div class="tab-content" id="tab-my-tab">
     <!-- Your content -->
   </div>
   ```

3. Tab automatically wired (JavaScript handles it)

**New API Endpoint**:

1. Add route in `web/app.py`:
   ```python
   @app.route('/api/my-endpoint')
   def api_my_endpoint():
       return jsonify({'success': True})
   ```

2. Call from frontend:
   ```javascript
   fetch('/api/my-endpoint')
     .then(r => r.json())
     .then(data => console.log(data));
   ```

---

## Mobile Support

**Responsive Breakpoints**:

- **Desktop**: 1920px+ (4 columns)
- **Laptop**: 1280-1920px (3 columns)
- **Tablet**: 768-1280px (2 columns)
- **Mobile**: <768px (1 column)

**Mobile Optimizations**:

- Touch-friendly buttons (min 44px)
- Larger tap targets
- Simplified navigation
- Stacked layouts

**Testing**:

```bash
# Test on different viewports
# Chrome DevTools → Toggle Device Toolbar (Cmd+Shift+M)
```

---

## Performance

### Metrics

- **Initial Load**: <2s (10 skills)
- **Search**: <100ms (real-time)
- **API Calls**: <500ms (local database)
- **Graduation**: <1s (file generation)

### Optimization

**Lazy Loading**:

Skills loaded on-demand (not all at once).

**Debounced Search**:

Search triggers after 300ms pause (reduces queries).

**Cached Data**:

Dashboard stats cached for 30s.

**Batch Updates**:

Multiple changes batched into single update.

---

## Security

### API Security

**No Authentication** (local only):

- Server binds to `0.0.0.0` (all interfaces)
- For production, add authentication
- Use Flask-Login or similar

**CSRF Protection**:

Not implemented (local use only). For production:

```python
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret'
csrf = CSRFProtect(app)
```

### Data Validation

**Input Validation**:

```python
skill_name = data.get('skill_name')
if not skill_name:
    return jsonify({'error': 'skill_name required'}), 400
```

**SQL Injection**:

Protected by parameterized queries in core modules.

---

## Troubleshooting

### Server Won't Start

**Problem**: `ModuleNotFoundError: No module named 'flask'`

**Fix**:

```bash
cd web
pip install -r requirements.txt
```

### Port Already in Use

**Problem**: `OSError: [Errno 48] Address already in use`

**Fix**:

```bash
# Find process on port 5000
lsof -i :5000

# Kill process
kill -9 <PID>

# Or use different port
python app.py --port 8080
```

### No Skills Showing

**Problem**: Dashboard shows 0 skills

**Fix**:

1. Check database:
   ```bash
   ls ~/.claude/auto-skill/
   # Should show: events.db, skill_tracker.db
   ```

2. Generate some skills:
   ```bash
   python run_detector.py
   ```

3. Refresh browser

### API Errors

**Problem**: 500 errors on API calls

**Fix**:

1. Check server logs in terminal

2. Verify database paths in `web/app.py`:
   ```python
   CONFIG = {
       'skills_dir': '~/.claude/skills/auto',  # Correct path?
       'tracker_db': '~/.claude/auto-skill/skill_tracker.db',
   }
   ```

3. Test API manually:
   ```bash
   curl http://localhost:5000/api/skills
   ```

---

## Deployment

### Development

```bash
cd web
python app.py
```

### Production (Linux)

**With Gunicorn**:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**With systemd**:

```ini
# /etc/systemd/system/auto-skill.service
[Unit]
Description=Claude Auto-Skill Web UI
After=network.target

[Service]
User=your-user
WorkingDirectory=/path/to/claude-auto-skill/web
ExecStart=/usr/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
sudo systemctl enable auto-skill
sudo systemctl start auto-skill
```

### Production (Docker)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY web/ /app/
RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Build and run:

```bash
docker build -t auto-skill-web .
docker run -p 5000:5000 -v ~/.claude:/root/.claude auto-skill-web
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name skills.example.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Future Features

Planned enhancements:

- [ ] Skill detail modal (full view)
- [ ] Confidence history charts (line graphs)
- [ ] Mental Model visualization (tree view)
- [ ] Skill comparison (side-by-side)
- [ ] Export/import (backup/restore)
- [ ] Dark mode toggle
- [ ] Multi-user support
- [ ] Real-time websockets (live updates)

---

## Next Steps

<div class="grid cards" markdown>

-   :material-cog: **[Configuration](../getting-started/configuration.md)**

    Customize paths and settings

-   :material-api: **[API Reference](../reference/api.md)**

    Complete API documentation

-   :material-rocket: **[Deployment Guide](../guide/workflows.md)**

    Production deployment strategies

</div>
