"""Unified setup command for rxiv-maker CLI."""

from pathlib import Path

import click
from rich.console import Console

from ..framework import SetupCommand

# Console instance for testing and utility access
console = Console()


@click.command()
@click.option(
    "--mode",
    type=click.Choice(["full", "python-only", "system-only", "minimal", "core"]),
    default="full",
    help="Setup mode: full (default), python-only, system-only, minimal, or core",
)
@click.option(
    "--reinstall",
    "-r",
    is_flag=True,
    help="Reinstall Python dependencies (removes .venv and creates new one)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force reinstallation of existing system dependencies",
)
@click.option(
    "--non-interactive",
    is_flag=True,
    help="Run in non-interactive mode",
)
@click.option(
    "--check-only",
    "-c",
    is_flag=True,
    help="Only check dependencies without installing",
)
@click.option(
    "--log-file",
    type=click.Path(path_type=Path),
    help="Path to log file for system dependency installation",
)
@click.pass_context
def setup(
    ctx: click.Context,
    mode: str,
    reinstall: bool,
    force: bool,
    non_interactive: bool,
    check_only: bool,
    log_file: Path | None,
) -> None:
    """Unified setup command for rxiv-maker.

    This intelligent setup command handles both Python and system dependencies
    based on the selected mode:

    - full: Complete setup (Python + all system dependencies)
    - python-only: Only Python packages and virtual environment
    - system-only: Only system dependencies (LaTeX, R, etc.)
    - minimal: Python + essential LaTeX only
    - core: Python + LaTeX (skip R)

    Examples:
        rxiv setup                    # Full setup
        rxiv setup --mode python-only    # Python dependencies only
        rxiv setup --check-only          # Check all dependencies
        rxiv setup --mode minimal --non-interactive    # Minimal headless setup
    """
    command = SetupCommand()
    return command.run(
        ctx,
        manuscript_path=None,
        mode=mode,
        reinstall=reinstall,
        force=force,
        non_interactive=non_interactive,
        check_only=check_only,
        log_file=str(log_file) if log_file else None,
    )
