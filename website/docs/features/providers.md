---
sidebar_position: 3
---

# Provider System

Auto-Skill uses a pluggable provider system for skill discovery. Providers implement the `SkillProvider` protocol and are orchestrated by the `ProviderManager`.

## Built-in Providers

### LocalProvider

Searches `~/.claude/skills/` for existing SKILL.md files. Parses YAML frontmatter to extract metadata.

### SkillsShProvider

Wraps the Skills.sh client to search 27,000+ community skills. Queries the [skills.sh](https://skills.sh) API for skill discovery, trending, and details.

### WellKnownProvider

Implements [RFC 8615](https://www.rfc-editor.org/rfc/rfc8615) discovery by fetching `/.well-known/agent-skills.json` from configured domains. Includes 15-minute response caching.

```bash
auto-skill discover --wellknown    # Include well-known discovery
```

## Custom Providers

Implement the `SkillProvider` protocol:

```python
from core.providers.base import SkillProvider, SkillSearchResult

class MyProvider:
    @property
    def name(self) -> str:
        return "my-provider"

    @property
    def source_id(self) -> str:
        return "custom"

    def is_available(self) -> bool:
        return True

    def search(self, query: str, limit: int = 10) -> list[SkillSearchResult]:
        # Return matching skills
        ...

    def get_skill_details(self, skill_id: str) -> dict | None:
        # Return full skill metadata
        ...
```

Register with the `ProviderManager`:

```python
from core.providers.manager import ProviderManager

manager = ProviderManager()
manager.register(MyProvider())
results = manager.search_all("payment", limit=10)
```

Providers are queried in registration order (first = highest priority). Failed providers are skipped gracefully.
