"""DEPRECATED: Install system dependencies command for rxiv-maker CLI.

This command is deprecated. Use 'rxiv setup --mode system-only' instead.
"""

from pathlib import Path

import click

from ..framework import DeprecatedInstallDepsCommand


@click.command()
@click.option(
    "--mode",
    type=click.Choice(["full", "minimal", "core", "skip-system"]),
    default="full",
    help="Installation mode (default: full)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force reinstallation of existing dependencies",
)
@click.option(
    "--non-interactive",
    is_flag=True,
    help="Run in non-interactive mode",
)
@click.option(
    "--repair",
    is_flag=True,
    help="Repair broken installation",
)
@click.option(
    "--log-file",
    type=click.Path(path_type=Path),
    help="Path to log file",
)
@click.pass_context
def install_deps(
    ctx: click.Context,
    mode: str,
    force: bool,
    non_interactive: bool,
    repair: bool,
    log_file: Path | None,
) -> None:
    """DEPRECATED: Install system dependencies for rxiv-maker.

    ⚠️  This command is deprecated and will be removed in a future version.

    Please use the unified setup command instead:
    - 'rxiv setup --mode system-only' (equivalent to this command)
    - 'rxiv setup' (full setup including Python dependencies)
    - 'rxiv setup --mode minimal' (minimal installation)

    See 'rxiv setup --help' for more options.
    """
    command = DeprecatedInstallDepsCommand()
    return command.run(
        ctx,
        manuscript_path=None,
        mode=mode,
        force=force,
        non_interactive=non_interactive,
        repair=repair,
        log_file=str(log_file) if log_file else None,
    )
