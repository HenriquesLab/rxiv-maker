"""Upgrade command for rxiv-maker CLI."""

import shlex
import subprocess
import sys

import click
from rich.console import Console

from ... import __version__
from ...utils.install_detector import detect_install_method, get_friendly_install_name, get_upgrade_command
from ...utils.update_checker import force_update_check

console = Console()


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

        if check_only:
            upgrade_cmd = get_upgrade_command(install_method)
            console.print(f"   Run: {upgrade_cmd}", style="blue")
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
        if not click.confirm("Do you want to continue?", default=True):
            console.print("❌ Upgrade cancelled", style="yellow")
            sys.exit(0)

    # Execute upgrade command
    console.print("\n🚀 Upgrading rxiv-maker...", style="blue")
    console.print(f"   Running: {upgrade_cmd}", style="dim")

    try:
        # Split compound commands (with &&) and run sequentially
        if " && " in upgrade_cmd:
            commands = upgrade_cmd.split(" && ")
            for cmd in commands:
                result = subprocess.run(
                    shlex.split(cmd),
                    check=False,
                    capture_output=False,  # Show output to user
                )
                if result.returncode != 0:
                    console.print(
                        f"\n⚠️  Command '{cmd}' exited with code {result.returncode}",
                        style="yellow",
                    )
                    console.print("   You may need to run the command manually:", style="yellow")
                    console.print(f"   {upgrade_cmd}", style="yellow")
                    sys.exit(result.returncode)
        else:
            # Single command - use shlex.split to avoid shell injection
            result = subprocess.run(
                shlex.split(upgrade_cmd),
                check=False,
                capture_output=False,  # Show output to user
            )
            if result.returncode != 0:
                console.print(
                    f"\n⚠️  Upgrade command exited with code {result.returncode}",
                    style="yellow",
                )
                console.print("   You may need to run the command manually:", style="yellow")
                console.print(f"   {upgrade_cmd}", style="yellow")
                sys.exit(result.returncode)

        console.print("\n✅ Upgrade completed successfully!", style="green")
        console.print("   Run 'rxiv --version' to verify the installation", style="blue")

    except subprocess.CalledProcessError as e:
        console.print(f"\n❌ Upgrade failed: {e}", style="red")
        console.print(f"   Try running manually: {upgrade_cmd}", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n❌ Unexpected error during upgrade: {e}", style="red")
        console.print(f"   Try running manually: {upgrade_cmd}", style="yellow")
        sys.exit(1)
