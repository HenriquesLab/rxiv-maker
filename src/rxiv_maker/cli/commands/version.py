"""Version command for rxiv-maker CLI."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ... import __version__
from ...utils.install_detector import detect_install_method, get_friendly_install_name, get_upgrade_command
from ...utils.platform import platform_detector

console = Console()


@click.command()
@click.option("--detailed", "-d", is_flag=True, help="Show detailed version information")
@click.option("--check-updates", "-u", is_flag=True, help="Check for available updates")
@click.pass_context
def version(ctx: click.Context, detailed: bool, check_updates: bool) -> None:
    """Show version information."""
    # Check for updates if requested
    if check_updates:
        console.print("🔍 Checking for updates...", style="blue")
        try:
            from ...utils.update_checker import force_update_check

            update_available, latest_version = force_update_check()

            if update_available:
                # Detect installation method and show appropriate upgrade command
                install_method = detect_install_method()
                upgrade_cmd = get_upgrade_command(install_method)
                install_name = get_friendly_install_name(install_method)

                console.print(f"📦 Update available: {__version__} → {latest_version}", style="green")
                console.print(f"   Installed via: {install_name}", style="blue")
                console.print(f"   Run: {upgrade_cmd}", style="blue")
            else:
                console.print(f"✅ You have the latest version ({__version__})", style="green")
        except Exception as e:
            console.print(f"⚠️  Could not check for updates: {e}", style="yellow")

    # Show version information
    if detailed:
        _show_detailed_version()
    else:
        console.print(f"rxiv-maker version {__version__}", style="bold blue")


def _show_detailed_version() -> None:
    """Show detailed version information."""
    table = Table(title=f"rxiv-maker {__version__} - Detailed Information")
    table.add_column("Component", style="cyan")
    table.add_column("Information", style="green")

    # Python version
    table.add_row("Python", f"{sys.version.split()[0]} ({sys.executable})")

    # Platform
    table.add_row("Platform", platform_detector.platform)
    table.add_row("Architecture", "Unknown")  # No architecture method available

    # Installation path
    try:
        import rxiv_maker

        install_path = Path(rxiv_maker.__file__).parent
        table.add_row("Installation Path", str(install_path))
    except Exception:
        table.add_row("Installation Path", "Unknown")

    console.print(table)
