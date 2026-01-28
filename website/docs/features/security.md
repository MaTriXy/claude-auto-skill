---
sidebar_position: 4
---

# Security

## Path Security

All skill names and file paths are validated before writing to disk.

### Name Sanitization

The `sanitize_name()` function enforces the [agentskills.io](https://agentskills.io) spec:

- Unicode NFKD normalization (e.g., `cafe-resume` from `café-résumé`)
- Lowercased, kebab-case only
- Max 64 characters
- Matches: `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$`
- Null bytes (`\x00`) stripped
- Path traversal sequences (`../`) blocked

### Path Validation

`is_path_safe()` resolves symlinks and verifies the target is within the allowed root directory. `safe_write()` combines validation and atomic writing.

### Symlink Safety

`is_safe_symlink()` verifies symlink targets don't escape the allowed directory boundary.

## Lock File Integrity

Skills are tracked in `~/.claude/auto-skill/skills.lock.json` with SHA-256 content hashes. Verify integrity:

```bash
auto-skill lock verify
```

The lock file uses atomic writes (temp file + `os.replace()`) to prevent corruption.

## Spec Compliance

The `validate_skill_md()` function checks generated skills against the agentskills.io specification:

- Name format and length
- Description under 1024 characters
- `allowed-tools` as YAML list (not comma-separated string)
- `version` field present
- Valid YAML frontmatter
