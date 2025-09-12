"""Version command for rxiv-maker CLI."""

import click

from ..framework import VersionCommand


@click.command()
@click.option("--detailed", "-d", is_flag=True, help="Show detailed version information")
@click.option("--check-updates", "-u", is_flag=True, help="Check for available updates")
@click.pass_context
def version(ctx: click.Context, detailed: bool, check_updates: bool) -> None:
    """Show version information."""
    command = VersionCommand()
    return command.run(ctx, manuscript_path=None, detailed=detailed, check_updates=check_updates)
