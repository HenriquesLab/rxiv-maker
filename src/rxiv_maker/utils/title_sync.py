"""Title synchronization between config and main manuscript file.

This module ensures that the title in the config file (rxiv.yml) and the
level 1 heading in the main manuscript file (01_MAIN.md) stay in sync.

Synchronization rules:
1. If title exists only in config → copy to main.md with auto-generated marker
2. If title exists only in main.md → copy to config
3. If both exist and differ → raise validation error
4. Auto-generated titles are marked with HTML comments for tracking
"""

import re
from pathlib import Path
from typing import Optional, Tuple

import yaml


class TitleSyncResult:
    """Result of title synchronization operation."""

    def __init__(self, success: bool, action: str, message: str, title: Optional[str] = None):
        """Initialize sync result.

        Args:
            success: Whether sync was successful
            action: Action taken ('no_change', 'synced_to_main', 'synced_to_config', 'mismatch')
            message: Human-readable description
            title: The synchronized title (if applicable)
        """
        self.success = success
        self.action = action
        self.message = message
        self.title = title


# Marker comment to identify auto-generated titles
AUTO_GENERATED_MARKER = "<!-- Title auto-synced from config (00_CONFIG.yml) by rxiv-maker -->"
MANUAL_WARNING_MARKER = "<!-- WARNING: Title differs from config. Update config or remove this heading. -->"


def extract_title_from_config(config_path: Path) -> Optional[str]:
    """Extract title from config file.

    Args:
        config_path: Path to rxiv.yml or similar config file

    Returns:
        Title string if found, None otherwise
    """
    if not config_path.exists():
        return None

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if not config or "title" not in config:
            return None

        title_data = config["title"]

        # Handle different title formats
        if isinstance(title_data, str):
            return title_data
        elif isinstance(title_data, dict):
            # Prefer 'long' title, fallback to 'short'
            return title_data.get("long") or title_data.get("short")
        elif isinstance(title_data, list):
            # Handle list format (legacy support)
            for item in title_data:
                if isinstance(item, dict) and "long" in item:
                    return item["long"]
            return None

        return None

    except Exception:
        return None


def extract_title_from_main(main_path: Path) -> Tuple[Optional[str], bool, int]:
    """Extract level 1 heading from main manuscript file.

    Args:
        main_path: Path to 01_MAIN.md

    Returns:
        Tuple of (title_text, is_auto_generated, line_number)
        - title_text: The title text if found, None otherwise
        - is_auto_generated: True if title has auto-generated marker
        - line_number: Line number where title was found (1-indexed), -1 if not found
    """
    if not main_path.exists():
        return None, False, -1

    try:
        with open(main_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")

        # Find first level 1 heading (# Title)
        # Skip YAML front matter
        in_yaml = False
        for i, line in enumerate(lines):
            if i == 0 and line.strip() == "---":
                in_yaml = True
                continue
            if in_yaml:
                if line.strip() == "---":
                    in_yaml = False
                continue

            # Check for level 1 heading
            match = re.match(r"^#\s+(.+)$", line)
            if match:
                title = match.group(1).strip()

                # Check if previous line or next line has auto-generated marker
                is_auto = False
                if i > 0 and AUTO_GENERATED_MARKER in lines[i - 1]:
                    is_auto = True
                elif i < len(lines) - 1 and AUTO_GENERATED_MARKER in lines[i + 1]:
                    is_auto = True

                return title, is_auto, i + 1

        return None, False, -1

    except Exception:
        return None, False, -1


def update_title_in_config(config_path: Path, title: str) -> bool:
    """Update title in config file.

    Args:
        config_path: Path to rxiv.yml
        title: New title to set

    Returns:
        True if successful, False otherwise
    """
    try:
        # Read existing config
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}

        # Update title (use string format for simplicity)
        config["title"] = title

        # Write back to file
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        return True

    except Exception:
        return False


def update_title_in_main(main_path: Path, title: str, is_auto_generated: bool = True) -> bool:
    """Update or add title in main manuscript file.

    Args:
        main_path: Path to 01_MAIN.md
        title: Title to set
        is_auto_generated: If True, adds auto-generated marker comment

    Returns:
        True if successful, False otherwise
    """
    try:
        if not main_path.exists():
            return False

        with open(main_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")

        # Find existing title and its location
        title_line = -1
        marker_line = -1
        in_yaml = False

        for i, line in enumerate(lines):
            if i == 0 and line.strip() == "---":
                in_yaml = True
                continue
            if in_yaml:
                if line.strip() == "---":
                    in_yaml = False
                continue

            # Check for level 1 heading
            if re.match(r"^#\s+", line):
                title_line = i
                # Check for marker in previous line
                if i > 0 and (AUTO_GENERATED_MARKER in lines[i - 1] or MANUAL_WARNING_MARKER in lines[i - 1]):
                    marker_line = i - 1
                break

        # Prepare new title lines
        marker = AUTO_GENERATED_MARKER if is_auto_generated else ""
        new_title = f"# {title}"

        if title_line >= 0:
            # Replace existing title
            lines[title_line] = new_title
            if marker and marker_line < 0:
                # Add marker if it doesn't exist
                lines.insert(title_line, marker)
            elif marker and marker_line >= 0:
                # Update existing marker
                lines[marker_line] = marker
            elif not marker and marker_line >= 0:
                # Remove auto-generated marker if title is now manual
                del lines[marker_line]
        else:
            # Add new title at the beginning (after YAML front matter if present)
            insert_pos = 0
            yaml_end = -1

            # Find end of YAML front matter
            if lines and lines[0].strip() == "---":
                for i, line in enumerate(lines[1:], 1):
                    if line.strip() == "---":
                        yaml_end = i
                        break

            if yaml_end >= 0:
                insert_pos = yaml_end + 1
                # Remove empty lines after YAML
                while insert_pos < len(lines) and not lines[insert_pos].strip():
                    del lines[insert_pos]
            else:
                # Remove leading empty lines
                while insert_pos < len(lines) and not lines[insert_pos].strip():
                    del lines[insert_pos]

            # Insert title and marker
            if marker:
                lines.insert(insert_pos, marker)
                lines.insert(insert_pos + 1, new_title)
            else:
                lines.insert(insert_pos, new_title)

            # Add blank line after title if next line isn't blank
            if insert_pos + (2 if marker else 1) < len(lines):
                next_line_idx = insert_pos + (2 if marker else 1)
                if lines[next_line_idx].strip():
                    lines.insert(next_line_idx, "")

        # Write back to file
        with open(main_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return True

    except Exception:
        return False


def remove_title_from_main(main_path: Path) -> bool:
    """Remove auto-generated title from main manuscript file.

    Only removes titles that have the auto-generated marker.

    Args:
        main_path: Path to 01_MAIN.md

    Returns:
        True if successful, False otherwise
    """
    try:
        if not main_path.exists():
            return False

        with open(main_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")

        # Find auto-generated title
        title_line = -1
        marker_line = -1

        for i, line in enumerate(lines):
            if AUTO_GENERATED_MARKER in line:
                marker_line = i
                # Title should be next line
                if i + 1 < len(lines) and re.match(r"^#\s+", lines[i + 1]):
                    title_line = i + 1
                    break

        if marker_line >= 0 and title_line >= 0:
            # Remove marker and title
            del lines[title_line]
            del lines[marker_line]

            # Remove extra blank line if present
            if marker_line < len(lines) and not lines[marker_line].strip():
                del lines[marker_line]

            # Write back to file
            with open(main_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

        return True

    except Exception:
        return False


def sync_titles(manuscript_path: Path, auto_sync: bool = True) -> TitleSyncResult:
    """Synchronize titles between config and main manuscript file.

    Args:
        manuscript_path: Path to manuscript directory
        auto_sync: If True, automatically sync titles. If False, only validate.

    Returns:
        TitleSyncResult with outcome of synchronization
    """
    # Try to find existing config file (check in order of preference)
    config_path = manuscript_path / "00_CONFIG.yml"
    if not config_path.exists():
        # Fallback to alternative config file names
        alt_paths = [
            manuscript_path / "rxiv.yml",
            manuscript_path / "rxiv.yaml",
        ]
        for alt_path in alt_paths:
            if alt_path.exists():
                config_path = alt_path
                break
        # else: keep config_path as 00_CONFIG.yml for creating new file

    main_path = manuscript_path / "01_MAIN.md"

    # Extract titles from both sources
    config_title = extract_title_from_config(config_path)
    main_title, is_auto_generated, line_num = extract_title_from_main(main_path)

    # Case 1: Both have titles
    if config_title and main_title:
        # Normalize for comparison (strip whitespace, compare case-insensitive)
        config_normalized = config_title.strip().lower()
        main_normalized = main_title.strip().lower()

        if config_normalized == main_normalized:
            return TitleSyncResult(
                success=True,
                action="no_change",
                message="Titles are already synchronized",
                title=config_title,
            )
        else:
            # Titles differ
            if is_auto_generated and auto_sync:
                # Auto-generated title is outdated, update it
                if update_title_in_main(main_path, config_title, is_auto_generated=True):
                    return TitleSyncResult(
                        success=True,
                        action="synced_to_main",
                        message=f"Updated auto-generated title in main to match config: '{config_title}'",
                        title=config_title,
                    )
                else:
                    return TitleSyncResult(
                        success=False,
                        action="error",
                        message="Failed to update title in main file",
                    )
            else:
                # Manual title differs from config - this is an error
                return TitleSyncResult(
                    success=False,
                    action="mismatch",
                    message=(
                        f"Title mismatch detected:\n"
                        f"  Config (rxiv.yml): '{config_title}'\n"
                        f"  Main (01_MAIN.md, line {line_num}): '{main_title}'\n"
                        f"Please update one to match the other, or remove the # heading from 01_MAIN.md"
                    ),
                )

    # Case 2: Only config has title
    elif config_title and not main_title:
        if auto_sync:
            if update_title_in_main(main_path, config_title, is_auto_generated=True):
                return TitleSyncResult(
                    success=True,
                    action="synced_to_main",
                    message=f"Added title to main from config: '{config_title}'",
                    title=config_title,
                )
            else:
                return TitleSyncResult(
                    success=False,
                    action="error",
                    message="Failed to add title to main file",
                )
        else:
            return TitleSyncResult(
                success=True,
                action="no_change",
                message="Title exists only in config (auto-sync disabled)",
                title=config_title,
            )

    # Case 3: Only main has title
    elif main_title and not config_title:
        if auto_sync and not is_auto_generated:
            # Copy manual title from main to config
            if update_title_in_config(config_path, main_title):
                return TitleSyncResult(
                    success=True,
                    action="synced_to_config",
                    message=f"Added title to config from main: '{main_title}'",
                    title=main_title,
                )
            else:
                return TitleSyncResult(
                    success=False,
                    action="error",
                    message="Failed to add title to config file",
                )
        else:
            return TitleSyncResult(
                success=True,
                action="no_change",
                message="Title exists only in main (auto-sync disabled or auto-generated)",
                title=main_title,
            )

    # Case 4: Neither has title
    else:
        return TitleSyncResult(
            success=True,
            action="no_change",
            message="No title found in config or main",
        )
