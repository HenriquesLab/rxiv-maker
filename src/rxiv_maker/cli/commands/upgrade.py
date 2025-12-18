"""Upgrade command for rxiv-maker CLI."""

import sys

import click
from henriqueslab_updater import handle_upgrade_workflow
from rich.console import Console

from ... import __version__
from ...utils.install_detector import detect_install_method
from ...utils.rich_upgrade_notifier import RxivUpgradeNotifier

console = Console()


@click.command()
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--check-only", "-c", is_flag=True, help="Only check for updates, don't upgrade")
@click.pass_context
def upgrade(ctx: click.Context, yes: bool, check_only: bool) -> None:
    """Upgrade rxiv-maker to the latest version.

    This command automatically detects how rxiv-maker was installed
    (Homebrew, pip, uv, pipx, etc.) and runs the appropriate upgrade command.

    Examples:
        rxiv upgrade              # Check and upgrade with confirmation
        rxiv upgrade --yes        # Upgrade without confirmation
        rxiv upgrade --check-only # Only check for updates
    """
    # Handle development installations specially
    install_method = detect_install_method()
    if install_method == "dev":
        console.print("⚠️  Development installation detected", style="yellow")
        console.print("   To update, pull the latest changes from git:", style="yellow")
        console.print("   [cyan]cd <repo> && git pull && uv sync[/cyan]", style="yellow")
        sys.exit(0)

    # Use centralized upgrade workflow
    notifier = RxivUpgradeNotifier(console)
    success, error = handle_upgrade_workflow(
        package_name="rxiv-maker",
        current_version=__version__,
        check_only=check_only,
        skip_confirmation=yes,
        notifier=notifier,
        github_org="HenriquesLab",
        github_repo="rxiv-maker",
    )

    if not success and error:
        sys.exit(1)
