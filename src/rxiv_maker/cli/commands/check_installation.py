"""CLI command for checking installation status."""

import click

from ..framework import CheckInstallationCommand


@click.command()
@click.option("--detailed", "-d", is_flag=True, help="Show detailed diagnostic information")
@click.option("--fix", is_flag=True, help="Attempt to fix missing dependencies")
@click.option("--json", is_flag=True, help="Output results in JSON format")
@click.pass_context
def check_installation(ctx: click.Context, detailed: bool, fix: bool, json: bool):
    """Check rxiv-maker installation and system dependencies.

    This command verifies that all required components are installed
    and working correctly, including Python packages, LaTeX,
    and other system dependencies.

    ## Examples

    **Basic installation check:**

        $ rxiv check-installation

    **Detailed diagnostics:**

        $ rxiv check-installation --detailed

    **JSON output for automation:**

        $ rxiv check-installation --json

    **Check and attempt fixes:**

        $ rxiv check-installation --fix
    """
    # Use centralized CheckInstallationCommand framework - eliminates 150+ lines!
    command = CheckInstallationCommand()
    command.run(ctx, detailed=detailed, fix=fix, json_output=json)
