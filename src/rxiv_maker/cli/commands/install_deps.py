"""DEPRECATED: Install system dependencies command for rxiv-maker CLI.

This command is deprecated. Use 'rxiv setup --mode system-only' instead.
"""

import sys
from pathlib import Path

import click
from rich.console import Console

console = Console()


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
    verbose = ctx.obj.get("verbose", False)

    # Show deprecation warning
    console.print("⚠️  WARNING: 'rxiv install-deps' is deprecated!", style="bold yellow")
    console.print("Use 'rxiv setup --mode system-only' instead.", style="yellow")
    console.print("Redirecting to the new command...", style="dim")
    console.print()

    try:
        # Import the new setup command
        from .setup import setup

        # Map parameters to the new setup command format
        setup_kwargs = {
            "mode": "system-only" if mode == "full" else mode,
            "reinstall": False,
            "force": force,
            "non_interactive": non_interactive,
            "check_only": False,
            "log_file": log_file,
        }

        # Call the new setup command
        setup(ctx, **setup_kwargs)

    except KeyboardInterrupt:
        console.print("\n⏹️  Installation interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error during installation: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)
