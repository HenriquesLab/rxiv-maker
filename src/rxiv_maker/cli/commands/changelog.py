"""Changelog command for rxiv-maker CLI."""

import sys

import click
from rich.console import Console

from ... import __version__
from ...utils.changelog_parser import (
    detect_breaking_changes,
    extract_highlights,
    fetch_changelog,
    format_summary,
    parse_version_entry,
)

console = Console()


@click.command()
@click.argument("version", required=False)
@click.option("--recent", "-r", type=int, metavar="N", help="Show last N versions (default: 5)")
@click.option("--since", "-s", metavar="VERSION", help="Show all versions since VERSION")
@click.option("--breaking-only", "-b", is_flag=True, help="Show only versions with breaking changes")
@click.option("--full", "-f", is_flag=True, help="Show complete changelog entry (not just highlights)")
def changelog(
    version: str | None,
    recent: int | None,
    since: str | None,
    breaking_only: bool,
    full: bool,
) -> None:
    r"""View changelog for rxiv-maker versions.

    \b
    Examples:
      rxiv changelog              # Show current version's changes
      rxiv changelog v1.13.0      # Show specific version
      rxiv changelog --recent 3   # Show last 3 versions
      rxiv changelog --since v1.10.0  # Show all since v1.10.0
      rxiv changelog --breaking-only  # Show only breaking changes
    """
    try:
        # Fetch full changelog
        console.print("📋 Fetching changelog...", style="blue")
        content = fetch_changelog()

        # Handle different modes
        if version:
            # Show specific version
            _show_version(content, version, full)
        elif since:
            # Show all since specified version
            _show_since(content, since, breaking_only, full)
        elif recent is not None:
            # Show last N versions
            _show_recent(content, recent if recent > 0 else 5, breaking_only, full)
        else:
            # Default: show current version
            _show_version(content, __version__, full)

    except Exception as e:
        console.print(f"❌ Error fetching changelog: {e}", style="red")
        console.print(
            "   View online: https://github.com/henriqueslab/rxiv-maker/blob/main/CHANGELOG.md",
            style="blue",
        )
        sys.exit(1)


def _show_version(content: str, version: str, full: bool) -> None:
    """Show changelog for a specific version.

    Args:
        content: Full CHANGELOG.md content
        version: Version to show
        full: Whether to show full entry or just highlights
    """
    entry = parse_version_entry(content, version)

    if not entry:
        console.print(f"❌ Version {version} not found in changelog", style="red")
        sys.exit(1)

    # Display version header
    if entry.date:
        console.print(f"\n📦 Version {entry.version} ({entry.date})", style="bold cyan")
    else:
        console.print(f"\n📦 Version {entry.version}", style="bold cyan")

    # Check for breaking changes
    breaking = detect_breaking_changes(entry)
    if breaking:
        console.print("\n⚠️  BREAKING CHANGES:", style="bold red")
        for change in breaking:
            console.print(f"  • {change}", style="yellow")
        console.print()

    if full:
        # Show complete entry
        _display_full_entry(entry)
    else:
        # Show highlights only
        highlights = extract_highlights(entry, limit=10)
        if highlights:
            console.print("Highlights:", style="bold")
            for emoji, description in highlights:
                console.print(f"  {emoji} {description}")
        else:
            console.print("No changes listed", style="dim")

    console.print(
        f"\nFull release: https://github.com/henriqueslab/rxiv-maker/releases/tag/v{entry.version}",
        style="blue",
    )


def _show_recent(content: str, count: int, breaking_only: bool, full: bool) -> None:
    """Show recent N versions.

    Args:
        content: Full CHANGELOG.md content
        count: Number of versions to show
        breaking_only: Whether to filter to only breaking changes
        full: Whether to show full entries or just highlights
    """
    # Get all versions

    from ...utils.changelog_parser import VERSION_HEADER_PATTERN

    matches = list(VERSION_HEADER_PATTERN.finditer(content))
    versions = [m.group(1) for m in matches]

    if not versions:
        console.print("❌ No versions found in changelog", style="red")
        sys.exit(1)

    # Limit to requested count
    versions_to_show = versions[:count]

    # Parse entries
    entries = []
    for version in versions_to_show:
        entry = parse_version_entry(content, version)
        if entry:
            # Filter by breaking changes if requested
            if breaking_only:
                if detect_breaking_changes(entry):
                    entries.append(entry)
            else:
                entries.append(entry)

    if not entries:
        if breaking_only:
            console.print(f"No breaking changes found in last {count} versions", style="yellow")
        else:
            console.print(f"No entries found for last {count} versions", style="yellow")
        sys.exit(0)

    # Display entries
    console.print(f"\n📋 Last {len(entries)} version(s):\n", style="bold cyan")

    if full:
        for i, entry in enumerate(entries):
            if i > 0:
                console.print("\n" + "─" * 80 + "\n", style="dim")
            _show_version(content, entry.version, full=True)
    else:
        summary = format_summary(entries, show_breaking=True, highlights_per_version=3)
        console.print(summary)


def _show_since(content: str, since_version: str, breaking_only: bool, full: bool) -> None:
    """Show all versions since specified version.

    Args:
        content: Full CHANGELOG.md content
        since_version: Version to start from (exclusive)
        breaking_only: Whether to filter to only breaking changes
        full: Whether to show full entries or just highlights
    """
    # Get all versions

    from ...utils.changelog_parser import VERSION_HEADER_PATTERN

    matches = list(VERSION_HEADER_PATTERN.finditer(content))
    all_versions = [m.group(1) for m in matches]

    # Normalize since_version
    since_version = since_version.lstrip("v")

    # Find index of since_version
    try:
        since_idx = all_versions.index(since_version)
    except ValueError:
        console.print(f"❌ Version {since_version} not found in changelog", style="red")
        sys.exit(1)

    # Get versions after since_version
    versions_to_show = all_versions[:since_idx]  # Newer versions come first

    if not versions_to_show:
        console.print(f"No versions found after v{since_version}", style="yellow")
        sys.exit(0)

    # Parse entries
    entries = []
    for version in versions_to_show:
        entry = parse_version_entry(content, version)
        if entry:
            # Filter by breaking changes if requested
            if breaking_only:
                if detect_breaking_changes(entry):
                    entries.append(entry)
            else:
                entries.append(entry)

    if not entries:
        if breaking_only:
            console.print(f"No breaking changes found since v{since_version}", style="yellow")
        else:
            console.print(f"No entries found since v{since_version}", style="yellow")
        sys.exit(0)

    # Display entries
    console.print(f"\n📋 Changes since v{since_version} ({len(entries)} version(s)):\n", style="bold cyan")

    if full:
        for i, entry in enumerate(entries):
            if i > 0:
                console.print("\n" + "─" * 80 + "\n", style="dim")
            _show_version(content, entry.version, full=True)
    else:
        summary = format_summary(entries, show_breaking=True, highlights_per_version=3)
        console.print(summary)


def _display_full_entry(entry) -> None:
    """Display full changelog entry with all sections.

    Args:
        entry: ChangelogEntry to display
    """
    # Display all sections
    for section_name, items in entry.sections.items():
        if items:
            console.print(f"\n{section_name}:", style="bold")
            for item in items:
                # Handle multi-line items
                lines = item.split("\n")
                console.print(f"  • {lines[0]}")
                for line in lines[1:]:
                    console.print(f"    {line}", style="dim")
