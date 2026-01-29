# Publishing auto-skill to PyPI

## ✅ Package Ready for Publishing

**Build Status:** ✅ Success
- Wheel: `auto_skill-3.0.0-py3-none-any.whl` (102K)
- Source: `auto_skill-3.0.0.tar.gz` (106K)
- Twine Check: ✅ PASSED
- CLI Test: ✅ Works (`auto-skill version`)

## Prerequisites

### 1. Create PyPI Account

**Test PyPI (for testing):**
- Register: https://test.pypi.org/account/register/
- API Token: https://test.pypi.org/manage/account/#api-tokens

**Production PyPI:**
- Register: https://pypi.org/account/register/
- API Token: https://pypi.org/manage/account/#api-tokens

### 2. Configure API Tokens

Create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-<your-production-token>

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-<your-test-token>
```

**Or use environment variables:**
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-<your-token>
```

## Publishing Steps

### Step 1: Clean Build

```bash
cd /tmp/auto-skill

# Clean old builds
rm -rf dist/ build/ *.egg-info

# Create fresh build environment
uv venv .venv-publish
source .venv-publish/bin/activate
uv pip install build twine
```

### Step 2: Build Package

```bash
python -m build
```

**Expected output:**
```
Successfully built auto_skill-3.0.0.tar.gz and auto_skill-3.0.0-py3-none-any.whl
```

### Step 3: Verify Package

```bash
twine check dist/*
```

**Expected:**
```
Checking dist/auto_skill-3.0.0-py3-none-any.whl: PASSED
Checking dist/auto_skill-3.0.0.tar.gz: PASSED
```

### Step 4: Test on TestPyPI (Recommended)

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ auto-skill

# Verify
auto-skill version
```

### Step 5: Publish to Production PyPI

```bash
# Upload to PyPI
twine upload dist/*
```

You'll see:
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading auto_skill-3.0.0-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 102.5/102.5 kB • 00:00
Uploading auto_skill-3.0.0.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 106.3/106.3 kB • 00:00

View at:
https://pypi.org/project/auto-skill/3.0.0/
```

### Step 6: Verify Installation

```bash
# Fresh environment
cd /tmp
python -m venv test-install
source test-install/bin/activate

# Install from PyPI
pip install auto-skill

# Verify
auto-skill version
# auto-skill 3.0.0
```

## After Publishing

### Update Documentation

**README.md:**
```markdown
## Installation

### Quick Install (PyPI)
\`\`\`bash
pip install auto-skill
\`\`\`

### For Agent Skills
\`\`\`bash
npx skills add MaTriXy/auto-skill
\`\`\`

### Complete Setup (Both)
\`\`\`bash
# 1. Install agent skills
npx skills add MaTriXy/auto-skill

# 2. Install CLI tool
pip install auto-skill

# 3. Verify
auto-skill version
\`\`\`
```

**Update install-cli.sh:**
```bash
# After PyPI publishing, update the repo URL in install-cli.sh:
REPO_URL="auto-skill"  # Instead of git+https://...
```

**Update SKILL.md:**
```markdown
## ⚙️ CLI Tool Installation

\`\`\`bash
# Option 1: Install from PyPI (recommended)
pip install auto-skill

# Option 2: With uv
uv pip install auto-skill

# Option 3: Run the included install script
bash ~/.agents/skills/auto-skill-guide/install-cli.sh
\`\`\`
```

### Create GitHub Release

Tag the release:
```bash
git tag v3.0.0
git push origin v3.0.0
```

Create release on GitHub with:
- Title: `v3.0.0 - PyPI Release`
- Description: Link to PyPI package
- Attach dist files

## Troubleshooting

### "Package already exists"
If version 3.0.0 is already published, bump the version:
1. Update version in `pyproject.toml`
2. Rebuild: `python -m build`
3. Upload new version

### "Invalid credentials"
- Verify API token is correct
- Check `~/.pypirc` format
- Try environment variables instead

### "Metadata validation failed"
Run `twine check dist/*` and fix reported issues

## Automation (Optional)

### GitHub Actions for Auto-Publishing

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine
      
      - name: Build package
        run: python -m build
      
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

Add `PYPI_API_TOKEN` to GitHub repository secrets.

## Post-Publishing Checklist

- [ ] Package appears on PyPI: https://pypi.org/project/auto-skill/
- [ ] `pip install auto-skill` works
- [ ] CLI command `auto-skill version` works
- [ ] README.md updated with PyPI install instructions
- [ ] install-cli.sh updated to use PyPI
- [ ] SKILL.md updated with PyPI instructions
- [ ] GitHub release created
- [ ] Announce on X/Twitter
- [ ] Update PR #15 with PyPI link

## Resources

- PyPI: https://pypi.org/
- TestPyPI: https://test.pypi.org/
- Packaging Guide: https://packaging.python.org/
- Twine Docs: https://twine.readthedocs.io/
