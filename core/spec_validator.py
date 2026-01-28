"""
Spec Validator - Validates rendered SKILL.md files against the agentskills.io spec.

Ensures generated skills conform to the specification:
- Name: kebab-case, max 64 chars, matches ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$
- Description: max 1024 chars
- allowed-tools: must be a YAML list (not comma-separated string)
- version: must be present
- Frontmatter: valid YAML between --- delimiters
"""

from typing import Optional

import yaml

from .path_security import SPEC_NAME_REGEX, MAX_NAME_LENGTH


# Max description length per agentskills.io spec
MAX_DESCRIPTION_LENGTH = 1024


class SpecViolation:
    """A single spec violation."""

    def __init__(self, field: str, message: str, severity: str = "error"):
        self.field = field
        self.message = message
        self.severity = severity  # "error" or "warning"

    def __repr__(self):
        return f"SpecViolation({self.severity}: {self.field}: {self.message})"


class SpecValidationResult:
    """Result of spec validation."""

    def __init__(self):
        self.violations: list[SpecViolation] = []

    @property
    def is_valid(self) -> bool:
        return not any(v.severity == "error" for v in self.violations)

    @property
    def errors(self) -> list[SpecViolation]:
        return [v for v in self.violations if v.severity == "error"]

    @property
    def warnings(self) -> list[SpecViolation]:
        return [v for v in self.violations if v.severity == "warning"]

    def add_error(self, field: str, message: str):
        self.violations.append(SpecViolation(field, message, "error"))

    def add_warning(self, field: str, message: str):
        self.violations.append(SpecViolation(field, message, "warning"))


def validate_skill_md(content: str) -> SpecValidationResult:
    """Validate a SKILL.md file content against the agentskills.io spec.

    Args:
        content: The full SKILL.md file content.

    Returns:
        SpecValidationResult with any violations found.
    """
    result = SpecValidationResult()

    # Parse frontmatter
    frontmatter = _extract_frontmatter(content)
    if frontmatter is None:
        result.add_error("frontmatter", "Missing or invalid YAML frontmatter (must be between --- delimiters)")
        return result

    # Validate name
    _validate_name(frontmatter, result)

    # Validate description
    _validate_description(frontmatter, result)

    # Validate allowed-tools
    _validate_allowed_tools(frontmatter, result)

    # Validate version
    _validate_version(frontmatter, result)

    return result


def _extract_frontmatter(content: str) -> Optional[dict]:
    """Extract and parse YAML frontmatter from SKILL.md content."""
    if not content.startswith("---"):
        return None

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None

    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return None


def _validate_name(frontmatter: dict, result: SpecValidationResult):
    """Validate the name field."""
    name = frontmatter.get("name")

    if not name:
        result.add_error("name", "Missing required field 'name'")
        return

    if not isinstance(name, str):
        result.add_error("name", f"Name must be a string, got {type(name).__name__}")
        return

    if len(name) > MAX_NAME_LENGTH:
        result.add_error("name", f"Name exceeds {MAX_NAME_LENGTH} chars (got {len(name)})")

    if not SPEC_NAME_REGEX.match(name):
        result.add_error(
            "name",
            f"Name '{name}' does not match spec regex ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$"
        )


def _validate_description(frontmatter: dict, result: SpecValidationResult):
    """Validate the description field."""
    desc = frontmatter.get("description")

    if not desc:
        result.add_error("description", "Missing required field 'description'")
        return

    if not isinstance(desc, str):
        result.add_error("description", f"Description must be a string, got {type(desc).__name__}")
        return

    if len(desc) > MAX_DESCRIPTION_LENGTH:
        result.add_error(
            "description",
            f"Description exceeds {MAX_DESCRIPTION_LENGTH} chars (got {len(desc)})"
        )


def _validate_allowed_tools(frontmatter: dict, result: SpecValidationResult):
    """Validate the allowed-tools field is a YAML list (not comma string)."""
    tools = frontmatter.get("allowed-tools")

    if tools is None:
        # allowed-tools is optional
        return

    if isinstance(tools, str):
        result.add_error(
            "allowed-tools",
            "Must be a YAML list, not a comma-separated string. "
            "Use:\n  allowed-tools:\n    - Tool1\n    - Tool2"
        )
        return

    if not isinstance(tools, list):
        result.add_error(
            "allowed-tools",
            f"Must be a YAML list, got {type(tools).__name__}"
        )
        return

    for item in tools:
        if not isinstance(item, str):
            result.add_error(
                "allowed-tools",
                f"Each tool must be a string, got {type(item).__name__}: {item}"
            )


def _validate_version(frontmatter: dict, result: SpecValidationResult):
    """Validate the version field."""
    version = frontmatter.get("version")

    if version is None:
        result.add_warning("version", "Missing 'version' field (recommended by spec)")
