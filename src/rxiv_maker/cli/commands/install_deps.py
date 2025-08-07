"""Install system dependencies command for rxiv-maker CLI."""

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
    """Install system dependencies for rxiv-maker.

    This command installs system-level dependencies like LaTeX, Node.js, R, and
    other libraries needed for manuscript processing. It's separate from the
    regular Python package installation to make dependency management explicit.

    Installation modes:
    - full: Install all dependencies (LaTeX, Node.js, R, system libs)
    - minimal: Python packages + essential LaTeX only
    - core: Python packages + LaTeX (skip Node.js, R)
    - skip-system: Python packages only
    """
    verbose = ctx.obj.get("verbose", False)

    try:
        # Import installation manager
        from ...install.manager import InstallManager, InstallMode

        # Create installation manager
        manager = InstallManager(
            mode=InstallMode(mode),
            verbose=verbose,
            force=force,
            interactive=not non_interactive,
            log_file=log_file,
        )

        console.print(f"🔧 Installing system dependencies in {mode} mode...", style="blue")

        # Run installation or repair
        success = manager.repair() if repair else manager.install()

        if success:
            console.print("✅ System dependency installation completed!", style="green")
            console.print("💡 Run 'rxiv check-installation' to verify setup", style="dim")
        else:
            console.print("❌ System dependency installation failed!", style="red")
            console.print("💡 Check the log file for details", style="dim")
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n⏹️  Installation interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error during installation: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)
