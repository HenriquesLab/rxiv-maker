"""Setup command for rxiv-maker CLI."""

import sys

import click
from rich.console import Console

console = Console()


@click.command()
@click.option(
    "--reinstall",
    "-r",
    is_flag=True,
    help="Reinstall Python dependencies (removes .venv and creates new one)",
)
@click.option("--check-deps-only", "-c", is_flag=True, help="Only check system dependencies")
@click.pass_context
def setup(ctx: click.Context, reinstall: bool, check_deps_only: bool) -> None:
    """Setup Python development environment.

    This command focuses on Python package installation and environment setup.
    For system dependencies (LaTeX, Node.js, R), use 'rxiv install-deps' instead.

    This command:
    - Installs Python dependencies
    - Sets up virtual environment
    - Checks existing system dependencies
    """
    verbose = ctx.obj.get("verbose", False)

    try:
        # Import setup environment command
        from ...engine.setup_environment import main as setup_environment_main

        # Prepare arguments
        args = []
        if reinstall:
            args.append("--reinstall")
        if check_deps_only:
            args.append("--check-deps-only")
        if verbose:
            args.append("--verbose")

        # Save original argv and replace
        original_argv = sys.argv
        sys.argv = ["setup_environment"] + args

        try:
            setup_environment_main()
            if check_deps_only:
                console.print("✅ Dependency check completed!", style="green")
            else:
                console.print("✅ Environment setup completed!", style="green")

        except SystemExit as e:
            if e.code != 0:
                console.print("❌ Setup failed. See details above.", style="red")
                sys.exit(1)

        finally:
            sys.argv = original_argv

    except KeyboardInterrupt:
        console.print("\n⏹️  Setup interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error during setup: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)
