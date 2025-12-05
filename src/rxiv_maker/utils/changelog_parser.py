"""Parse and extract information from CHANGELOG.md.

This module provides functionality to fetch, parse, and format changelog entries
for display in update notifications and CLI commands.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class ChangelogSection:
    """Represents a section in a changelog entry (Added, Changed, Fixed, etc.)."""

    title: str  # e.g., "Added", "Changed", "Fixed"
    items: List[str]  # List of change descriptions


@dataclass
class ChangelogEntry:
    """Represents a complete changelog entry for a specific version."""

    version: str  # e.g., "1.13.0"
    date: Optional[str]  # e.g., "2025-11-24"
    sections: Dict[str, List[str]]  # Section title -> list of changes
    raw_content: str  # Original markdown content


# Regular expressions for parsing
VERSION_HEADER_PATTERN = re.compile(r"^## \[v?([\d.]+)\](?:\s*-\s*(\d{4}-\d{2}-\d{2}))?", re.MULTILINE)
SECTION_HEADER_PATTERN = re.compile(
    r"^### (Added|Changed|Fixed|Removed|Documentation|Deprecated|Security)", re.MULTILINE
)
BREAKING_PATTERNS = [
    re.compile(r"\*\*BREAKING", re.IGNORECASE),
    re.compile(r"breaking change", re.IGNORECASE),
    re.compile(r"⚠️", re.MULTILINE),
    re.compile(r"### Migration", re.MULTILINE),
]

# Default changelog URL
DEFAULT_CHANGELOG_URL = "https://raw.githubusercontent.com/HenriquesLab/rxiv-maker/main/CHANGELOG.md"


def fetch_changelog(url: str = DEFAULT_CHANGELOG_URL, timeout: int = 5) -> str:
    """Fetch CHANGELOG.md content from URL.

    Args:
        url: URL to fetch changelog from
        timeout: Request timeout in seconds

    Returns:
        Raw changelog content as string

    Raises:
        URLError: If network request fails
        HTTPError: If HTTP request returns error status
    """
    req = Request(url, headers={"User-Agent": "rxiv-maker-update-checker"})
    with urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8")


def parse_version_entry(content: str, version: str) -> Optional[ChangelogEntry]:
    """Parse a specific version's changelog entry.

    Args:
        content: Full CHANGELOG.md content
        version: Version to extract (e.g., "1.13.0" or "v1.13.0")

    Returns:
        ChangelogEntry if found, None otherwise
    """
    # Normalize version (remove 'v' prefix if present)
    version = version.lstrip("v")

    # Find all version headers
    version_matches = list(VERSION_HEADER_PATTERN.finditer(content))

    # Find the target version
    target_match = None
    next_match = None

    for i, match in enumerate(version_matches):
        if match.group(1) == version:
            target_match = match
            if i + 1 < len(version_matches):
                next_match = version_matches[i + 1]
            break

    if not target_match:
        return None

    # Extract content between this version and the next
    start_pos = target_match.end()
    end_pos = next_match.start() if next_match else len(content)
    entry_content = content[start_pos:end_pos].strip()

    # Parse sections
    sections = parse_sections(entry_content)

    return ChangelogEntry(
        version=version,
        date=target_match.group(2),
        sections=sections,
        raw_content=entry_content,
    )


def parse_sections(content: str) -> Dict[str, List[str]]:
    """Parse changelog sections (Added, Changed, Fixed, etc.).

    Args:
        content: Changelog entry content

    Returns:
        Dictionary mapping section names to lists of changes
    """
    sections = {}
    current_section = None
    current_items = []

    for line in content.split("\n"):
        # Check if this is a section header
        section_match = SECTION_HEADER_PATTERN.match(line)
        if section_match:
            # Save previous section
            if current_section:
                sections[current_section] = current_items

            # Start new section
            current_section = section_match.group(1)
            current_items = []
            continue

        # Check if this is a list item
        if current_section and line.strip().startswith("-"):
            # Extract the item text (remove leading "- " and "* ")
            item = line.strip().lstrip("-").lstrip("*").strip()
            if item:
                current_items.append(item)

    # Save last section
    if current_section:
        sections[current_section] = current_items

    return sections


def extract_highlights(entry: ChangelogEntry, limit: int = 3) -> List[Tuple[str, str]]:
    """Extract the most important highlights from a changelog entry.

    Prioritizes: Added > Changed > Fixed > Others

    Args:
        entry: Changelog entry to extract from
        limit: Maximum number of highlights to return

    Returns:
        List of (emoji, description) tuples
    """
    highlights = []

    # Priority order for sections
    priority_sections = [
        ("Added", "✨"),
        ("Changed", "🔄"),
        ("Fixed", "🐛"),
        ("Removed", "🗑️"),
        ("Security", "🔒"),
        ("Documentation", "📝"),
    ]

    for section_name, emoji in priority_sections:
        if section_name in entry.sections:
            items = entry.sections[section_name]
            for item in items:
                if len(highlights) >= limit:
                    break

                # Extract first line/sentence of item (before sub-bullets)
                lines = item.split("\n")
                first_line = lines[0].strip()

                # Remove markdown bold markers
                first_line = first_line.replace("**", "")

                # Truncate if too long
                if len(first_line) > 80:
                    first_line = first_line[:77] + "..."

                highlights.append((emoji, first_line))

            if len(highlights) >= limit:
                break

    return highlights[:limit]


def detect_breaking_changes(entry: ChangelogEntry) -> List[str]:
    """Detect breaking changes in a changelog entry.

    Args:
        entry: Changelog entry to check

    Returns:
        List of breaking change descriptions
    """
    breaking_changes = []

    # Check for breaking changes in any section
    for _section_name, items in entry.sections.items():
        for item in items:
            # Check if item contains breaking change indicators
            for pattern in BREAKING_PATTERNS:
                if pattern.search(item):
                    # Extract the breaking change description
                    lines = item.split("\n")
                    first_line = lines[0].strip().replace("**", "")

                    # Remove BREAKING prefix if present
                    first_line = re.sub(r"^\*\*BREAKING:?\*\*\s*", "", first_line, flags=re.IGNORECASE)
                    first_line = re.sub(r"^BREAKING:?\s*", "", first_line, flags=re.IGNORECASE)

                    breaking_changes.append(first_line)
                    break  # Don't add same item multiple times

    return breaking_changes


def get_versions_between(content: str, current: str, latest: str) -> List[str]:
    """Get all versions between current and latest (inclusive of latest).

    Args:
        content: Full CHANGELOG.md content
        current: Current version (e.g., "1.10.0")
        latest: Latest version (e.g., "1.13.0")

    Returns:
        List of version strings in chronological order (oldest to newest)
    """
    # Normalize versions
    current = current.lstrip("v")
    latest = latest.lstrip("v")

    # Find all versions
    version_matches = VERSION_HEADER_PATTERN.findall(content)
    all_versions = [v[0] for v in version_matches]  # v[0] is the version, v[1] is the date

    # Find indices
    try:
        current_idx = all_versions.index(current)
        latest_idx = all_versions.index(latest)
    except ValueError:
        # If version not found, return empty list
        return []

    # Extract versions between (inclusive of latest, exclusive of current)
    # Reverse order since changelog is newest-first
    if latest_idx < current_idx:
        between_versions = all_versions[latest_idx:current_idx]
        return list(reversed(between_versions))  # Return chronological order
    else:
        return []


def format_summary(
    entries: List[ChangelogEntry],
    show_breaking: bool = True,
    highlights_per_version: int = 3,
) -> str:
    """Format changelog entries for terminal display with rich markup.

    Args:
        entries: List of changelog entries to format
        show_breaking: Whether to show breaking changes prominently
        highlights_per_version: Number of highlights per version

    Returns:
        Formatted string for terminal display with rich markup
    """
    lines = []

    # Collect all breaking changes first
    all_breaking = []
    for entry in entries:
        breaking = detect_breaking_changes(entry)
        if breaking:
            all_breaking.extend([(entry.version, b) for b in breaking])

    # Show breaking changes prominently if present
    if show_breaking and all_breaking:
        lines.append("[bold red]⚠️  BREAKING CHANGES:[/bold red]")
        for version, change in all_breaking:
            lines.append(f"  [red]•[/red] {change} [dim](v{version})[/dim]")
        lines.append("")

    # Show highlights for each version
    if entries:
        lines.append("[bold bright_cyan]✨ What's New:[/bold bright_cyan]")
        lines.append("")

    for entry in entries:
        # Version header with date - use gradient colors
        if entry.date:
            lines.append(f"  [bold yellow]v{entry.version}[/bold yellow] [dim]({entry.date})[/dim]:")
        else:
            lines.append(f"  [bold yellow]v{entry.version}[/bold yellow]:")

        # Highlights with colored emojis and descriptions
        highlights = extract_highlights(entry, limit=highlights_per_version)
        for emoji, description in highlights:
            lines.append(f"    [bright_white]{emoji}[/bright_white] [dim]{description}[/dim]")

        lines.append("")  # Blank line between versions

    return "\n".join(lines).rstrip()


def fetch_and_format_changelog(
    current_version: str,
    latest_version: str,
    changelog_url: str = DEFAULT_CHANGELOG_URL,
    highlights_per_version: int = 3,
) -> Tuple[Optional[str], Optional[str]]:
    """Fetch changelog and format summary for version range.

    This is the main convenience function that combines all steps.

    Args:
        current_version: Current installed version
        latest_version: Latest available version
        changelog_url: URL to fetch changelog from
        highlights_per_version: Number of highlights per version

    Returns:
        Tuple of (formatted_summary, error_message)
        If successful, returns (summary, None)
        If failed, returns (None, error_message)
    """
    try:
        # Fetch changelog
        content = fetch_changelog(changelog_url, timeout=5)

        # Get versions between
        versions = get_versions_between(content, current_version, latest_version)

        if not versions:
            return None, f"No changelog entries found between v{current_version} and v{latest_version}"

        # Parse entries
        entries = []
        for version in versions:
            entry = parse_version_entry(content, version)
            if entry:
                entries.append(entry)

        if not entries:
            return None, "Could not parse changelog entries"

        # Format summary
        summary = format_summary(entries, show_breaking=True, highlights_per_version=highlights_per_version)

        return summary, None

    except (URLError, HTTPError) as e:
        return None, f"Failed to fetch changelog: {e}"
    except Exception as e:
        return None, f"Error parsing changelog: {e}"
