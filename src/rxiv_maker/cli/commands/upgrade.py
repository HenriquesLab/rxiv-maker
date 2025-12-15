"""Upgrade command for rxiv-maker CLI."""

import sys

import click
from henriqueslab_updater import execute_upgrade, force_update_check
from rich.console import Console

from ... import __version__
from ...utils.changelog_parser import fetch_and_format_changelog
from ...utils.install_detector import detect_install_method, get_friendly_install_name, get_upgrade_command
from ..interactive import prompt_confirm

console = Console()


def _display_changelog(console: Console, current_version: str, latest_version: str) -> None:
    """Display changelog summary for version range.

    Args:
        console: Rich console for output
        current_version: Current installed version
        latest_version: Latest available version
    """
    console.print("\n📋 What's changing:", style="bold blue")

    # Fetch changelog summary
    summary, error = fetch_and_format_changelog(
        current_version=current_version,
        latest_version=latest_version,
        highlights_per_version=3,
    )

    if error:
        console.print("   Unable to fetch changelog details", style="dim yellow")
        console.print(
            f"   View online: https://github.com/henriqueslab/rxiv-maker/releases/tag/v{latest_version}",
            style="dim blue",
        )
        return

    if summary:
        # Display the changelog with proper formatting
        for line in summary.split("\n"):
            if line.startswith("⚠️"):
                # Highlight breaking changes prominently
                console.print(line, style="bold red")
            elif line.startswith("What's New:"):
                console.print(line, style="bold cyan")
            elif line.startswith("  v"):
                # Version headers
                console.print(line, style="bold yellow")
            elif line.strip().startswith(("✨", "🔄", "🐛", "🗑️", "🔒", "📝")):
                # Change items
                console.print(f"   {line.strip()}", style="white")
            elif line.strip().startswith("•"):
                # Breaking change items
                console.print(f"   {line.strip()}", style="yellow")
            elif line.strip():
                console.print(f"   {line}", style="dim")
    else:
        console.print("   No detailed changelog available", style="dim")


@click.command()
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--check-only", "-c", is_flag=True, help="Only check for updates, don't upgrade")
@click.pass_context
def upgrade(ctx: click.Context, yes: bool, check_only: bool) -> None:
    """Upgrade rxiv-maker to the latest version.

    This command automatically detects how rxiv-maker was installed
    (Homebrew, pip, uv, pipx, etc.) and runs the appropriate upgrade command.
    """
    # Detect installation method
    install_method = detect_install_method()
    install_name = get_friendly_install_name(install_method)

    console.print(f"🔍 Detected installation method: {install_name}", style="blue")

    # Handle development installations
    if install_method == "dev":
        console.print("⚠️  Development installation detected", style="yellow")
        console.print("   To update, pull the latest changes from git:", style="yellow")
        console.print("   cd <repo> && git pull && uv sync", style="yellow")
        sys.exit(0)

    # Check for updates
    console.print("🔍 Checking for updates...", style="blue")
    try:
        update_available, latest_version = force_update_check()

        if not update_available:
            console.print(f"✅ You already have the latest version ({__version__})", style="green")
            sys.exit(0)

        console.print(f"📦 Update available: {__version__} → {latest_version}", style="green")

        # Fetch and display changelog
        _display_changelog(console, __version__, latest_version)

        if check_only:
            upgrade_cmd = get_upgrade_command(install_method)
            console.print(f"\n   Run: {upgrade_cmd}", style="blue")
            sys.exit(0)

    except Exception as e:
        console.print(f"⚠️  Could not check for updates: {e}", style="yellow")
        console.print("   Proceeding with upgrade attempt...", style="yellow")
        latest_version = "latest"

    # Get upgrade command
    upgrade_cmd = get_upgrade_command(install_method)

    # Show confirmation
    if not yes:
        console.print(f"\n📦 About to run: {upgrade_cmd}", style="blue")
        if not prompt_confirm("Do you want to continue?", default=True):
            console.print("❌ Upgrade cancelled", style="yellow")
            sys.exit(0)

    # Execute upgrade command using centralized executor
    console.print("\n🚀 Upgrading rxiv-maker...", style="blue")
    console.print(f"   Running: {upgrade_cmd}", style="dim")

    success, error = execute_upgrade(upgrade_cmd, show_output=True, timeout=300)

    if success:
        console.print("\n✅ Upgrade completed successfully!", style="green")
        console.print("   Run 'rxiv --version' to verify the installation", style="blue")

        # Show what's new in the upgraded version
        if latest_version != "latest":
            console.print(f"\n🎉 What's new in v{latest_version}:", style="bold green")
            console.print(
                f"   View full changelog: https://github.com/henriqueslab/rxiv-maker/releases/tag/v{latest_version}",
                style="blue",
            )
    else:
        console.print(f"\n❌ Upgrade failed: {error}", style="red")
        console.print(f"   Try running manually: {upgrade_cmd}", style="yellow")
        sys.exit(1)
