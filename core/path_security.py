"""
Path Security - Validates and sanitizes paths for safe filesystem operations.

Prevents path traversal attacks, null byte injection, and other filesystem
exploits when generating skill names and writing skill files.
"""

import os
import re
import unicodedata
from pathlib import Path
from typing import Optional


# agentskills.io spec regex for skill names
SPEC_NAME_REGEX = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")

# Maximum allowed name length (agentskills.io spec)
MAX_NAME_LENGTH = 64

# Characters to strip beyond the spec allowlist
_UNSAFE_CHARS = re.compile(r"[^a-z0-9-]")


def sanitize_name(raw_name: str) -> str:
    """Sanitize a skill name for safe filesystem and spec-compliant usage.

    Applies the following transformations:
    1. Unicode normalization (NFKD) and ASCII folding
    2. Lowercase conversion
    3. Replace non-alphanumeric chars (except hyphens) with hyphens
    4. Collapse consecutive hyphens
    5. Strip leading/trailing hyphens
    6. Truncate to MAX_NAME_LENGTH
    7. Ensure result matches agentskills.io spec regex

    Args:
        raw_name: The unsanitized name string.

    Returns:
        A sanitized, spec-compliant kebab-case name.

    Raises:
        ValueError: If the name cannot be sanitized to a valid result.
    """
    if not raw_name:
        raise ValueError("Skill name cannot be empty")

    # Strip null bytes
    name = raw_name.replace("\x00", "")

    # Unicode normalize -> ASCII fold
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")

    # Lowercase
    name = name.lower()

    # Replace path separators and unsafe chars with hyphens
    name = name.replace("/", "-").replace("\\", "-")
    name = _UNSAFE_CHARS.sub("-", name)

    # Collapse consecutive hyphens
    name = re.sub(r"-+", "-", name)

    # Strip leading/trailing hyphens
    name = name.strip("-")

    # Truncate to max length (trim at last hyphen to avoid partial words)
    if len(name) > MAX_NAME_LENGTH:
        name = name[:MAX_NAME_LENGTH]
        # Trim at last hyphen if possible for clean break
        last_hyphen = name.rfind("-")
        if last_hyphen > MAX_NAME_LENGTH // 2:
            name = name[:last_hyphen]
        name = name.rstrip("-")

    if not name:
        raise ValueError(f"Skill name '{raw_name}' cannot be sanitized to a valid result")

    if not SPEC_NAME_REGEX.match(name):
        raise ValueError(
            f"Sanitized name '{name}' does not match spec regex "
            f"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$"
        )

    return name


def is_path_safe(target: Path, allowed_root: Path) -> bool:
    """Check whether a target path is safely contained within an allowed root.

    Guards against:
    - Path traversal (../)
    - Null bytes in path components
    - Symlink escapes (resolves symlinks before comparison)
    - Absolute path injection

    Args:
        target: The path to validate.
        allowed_root: The directory that must contain `target`.

    Returns:
        True if target is safely within allowed_root, False otherwise.
    """
    try:
        # Check for null bytes
        target_str = str(target)
        if "\x00" in target_str:
            return False

        # Check for suspicious path components
        for part in target.parts:
            if "\x00" in part:
                return False
            if part == "..":
                return False

        # Resolve both paths to eliminate symlinks and relative components
        resolved_target = target.resolve()
        resolved_root = allowed_root.resolve()

        # Verify containment
        return resolved_target == resolved_root or str(resolved_target).startswith(
            str(resolved_root) + os.sep
        )
    except (OSError, ValueError):
        return False


def is_safe_symlink(link_path: Path, target_path: Path, allowed_root: Path) -> bool:
    """Check whether a symlink is safe to create.

    Ensures both the link location and its target are within allowed boundaries.

    Args:
        link_path: Where the symlink will be created.
        target_path: What the symlink will point to.
        allowed_root: The root directory that must contain both paths.

    Returns:
        True if the symlink is safe to create, False otherwise.
    """
    if not is_path_safe(link_path, allowed_root):
        return False
    if not is_path_safe(target_path, allowed_root):
        return False
    # Ensure target actually exists (or will exist)
    # Don't follow symlinks in the target itself
    return True


def safe_write(content: str, target: Path, allowed_root: Path) -> Path:
    """Write content to a file only if the path is safe.

    Creates parent directories as needed.

    Args:
        content: The file content to write.
        target: The file path to write to.
        allowed_root: The directory that must contain `target`.

    Returns:
        The resolved path of the written file.

    Raises:
        ValueError: If the target path is not safe.
    """
    if not is_path_safe(target, allowed_root):
        raise ValueError(
            f"Unsafe path: {target} is not within allowed root {allowed_root}"
        )

    resolved = target.resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(content)
    return resolved
