# Screenshot Guide

This file documents which screenshots are needed for the documentation.

## Required Screenshots

### 1. Dashboard (dashboard.png)
**Location**: Home page after login  
**URL**: `http://localhost:5000`  
**Capture**: Full page view showing:
- Stats cards (Total Skills, Local, External, Usage, Success Rate)
- All Skills tab active
- 3-4 skill cards visible
- Search box
- Sidebar navigation

**Settings**:
- Browser: Chrome/Firefox (1920x1080)
- Zoom: 100%
- Show: Dashboard with real data

### 2. Skill Browser (skill-browser.png)
**Location**: All Skills tab  
**URL**: `http://localhost:5000#skills`  
**Capture**: Skill cards grid showing:
- Multiple skill cards (6-8 visible)
- Different confidence levels (colors)
- Source badges (local/external)
- Hover effect on one card
- Search with results

**Settings**:
- Show variety of skills
- Confidence bars at different levels
- Mix of local and external skills

### 3. Graduation Tab (graduation.png)
**Location**: Graduation tab  
**URL**: `http://localhost:5000#graduation`  
**Capture**: Graduation candidates showing:
- 2-3 candidate cards
- Candidate details (confidence, usage, success rate)
- "Graduate to Local" button
- Criteria explanation at top

**Settings**:
- Show skills that meet graduation criteria
- Highlight the CTA button

### 4. Publishing Tab (publishing.png)
**Location**: Publishing tab  
**URL**: `http://localhost:5000#publish`  
**Capture**: Publishable skills showing:
- 2-3 publishable skill cards
- "Publish to skills.sh" buttons
- Status indicators

### 5. Skill Detail Modal (skill-detail.png)
**Location**: Click a skill card  
**URL**: Modal overlay  
**Capture**: Detailed skill view showing:
- Full skill name and description
- Confidence history chart
- Usage statistics
- Tool sequence
- Success indicators

### 6. CLI Output (cli-discover.png)
**Terminal screenshot**:
```bash
python -m commands.discover
```
**Capture**: Terminal showing:
- Command execution
- Discovered skills list
- Confidence percentages
- Source indicators
- Colorized output

### 7. CLI Graduation (cli-graduation.png)
**Terminal screenshot**:
```bash
python -m core.graduation_manager
```
**Capture**: Terminal showing:
- Graduation candidates list
- Interactive prompt
- Success message after graduation

### 8. Mental Model Integration (mental-integration.png)
**Terminal screenshot showing**:
```bash
mental show
python -m commands.discover --domain Payment
```
**Capture**: Terminal showing:
- Mental domains/capabilities
- Skills suggested for domain
- Mental context in skill metadata

## How to Capture

### For Web UI Screenshots

1. **Start server**:
   ```bash
   cd web
   python app.py
   ```

2. **Open browser**: Navigate to `http://localhost:5000`

3. **Capture**:
   - macOS: `Cmd+Shift+4` then Space (window capture)
   - Windows: `Win+Shift+S` (Snipping Tool)
   - Linux: `gnome-screenshot -w` or Screenshot tool

4. **Optimize**:
   ```bash
   # Convert to PNG (if needed)
   convert screenshot.jpg screenshot.png
   
   # Optimize file size
   optipng screenshot.png
   ```

5. **Place in**: `docs/assets/screenshots/`

### For Terminal Screenshots

1. **Set terminal size**: 120x30 characters

2. **Set theme**: Dark theme with good contrast

3. **Capture**: Use macOS Screenshot or equivalent

4. **Crop**: Remove unnecessary margins

5. **Optimize**: Convert to PNG if needed

## Naming Convention

- `dashboard.png` - Main dashboard
- `skill-browser.png` - Skill browser view
- `graduation.png` - Graduation tab
- `publishing.png` - Publishing tab
- `skill-detail.png` - Skill detail modal
- `cli-discover.png` - CLI discover command
- `cli-graduation.png` - CLI graduation command
- `mental-integration.png` - Mental Model integration

## Image Specs

- **Format**: PNG (for screenshots with text)
- **Max Width**: 1920px
- **Optimize**: Use optipng or similar
- **File Size**: Target <500KB per image

## Banner Image

Create a banner for the home page:

**File**: `docs/assets/banner.png`

**Specs**:
- Dimensions: 1200x400px
- Style: Purple gradient background
- Text: "Claude Auto-Skill" with otter emoji 🦦
- Tagline: "Learn from your workflows"
- Include: Pattern detection visual + confidence evolution diagram

**Tools**:
- Figma (recommended)
- Canva
- GIMP
- Photoshop

---

## TODO

- [ ] Capture all web UI screenshots
- [ ] Capture CLI screenshots
- [ ] Create banner image
- [ ] Optimize all images (<500KB)
- [ ] Verify all paths in docs
- [ ] Test image loading in MkDocs

---

**After capturing screenshots**, update the following files:

1. `docs/index.md` - Verify image paths
2. `docs/features/web-ui.md` - Add screenshots
3. `docs/getting-started/quick-start.md` - Add CLI screenshots
4. `README.md` - Add banner and preview images
