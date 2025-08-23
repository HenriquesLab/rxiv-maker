"""Unified setup command for rxiv-maker CLI."""

import sys
from pathlib import Path

import click
from rich.console import Console

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
    - system-only: Only system dependencies (LaTeX, Node.js, R, etc.)
    - minimal: Python + essential LaTeX only
    - core: Python + LaTeX (skip Node.js, R)

    Examples:
        rxiv setup                    # Full setup
        rxiv setup --mode python-only    # Python dependencies only
        rxiv setup --check-only          # Check all dependencies
        rxiv setup --mode minimal --non-interactive    # Minimal headless setup
    """
    verbose = ctx.obj.get("verbose", False)

    # Show what we're about to do
    if check_only:
        console.print(f"🔍 Checking dependencies in {mode} mode...", style="blue")
    else:
        console.print(f"🔧 Setting up rxiv-maker in {mode} mode...", style="blue")

    try:
        python_success = True
        system_success = True

        # Handle Python dependencies (unless system-only mode)
        if mode != "system-only":
            try:
                from ...engines.operations.setup_environment import main as setup_environment_main

                # Prepare arguments for Python setup
                args = []
                if reinstall:
                    args.append("--reinstall")
                if check_only:
                    args.append("--check-deps-only")
                if verbose:
                    args.append("--verbose")

                # Save original argv and replace
                original_argv = sys.argv
                sys.argv = ["setup_environment"] + args

                try:
                    setup_environment_main()
                    if not check_only:
                        console.print("✅ Python environment setup completed!", style="green")

                except SystemExit as e:
                    if e.code != 0:
                        python_success = False
                        console.print("❌ Python setup failed!", style="red")

                finally:
                    sys.argv = original_argv

            except Exception as e:
                python_success = False
                console.print(f"❌ Python setup error: {e}", style="red")

        # Handle system dependencies (unless python-only mode)
        if mode != "python-only":
            try:
                from ...core.managers.install_manager import InstallManager, InstallMode

                # Map setup modes to install modes
                install_mode_map = {
                    "full": "full",
                    "system-only": "full",
                    "minimal": "minimal",
                    "core": "core",
                }
                install_mode = install_mode_map.get(mode, "full")

                # Create installation manager
                manager = InstallManager(
                    mode=InstallMode(install_mode),
                    verbose=verbose,
                    force=force,
                    interactive=not non_interactive,
                    log_file=log_file,
                )

                if check_only:
                    # Just check system dependencies
                    from ...install.utils.verification import verify_installation

                    verification_results = verify_installation(verbose=verbose)

                    # Check if all required components are available
                    failed_components = [comp for comp, status in verification_results.items() if not status]
                    if failed_components:
                        system_success = False
                        console.print(f"❌ Missing system dependencies: {', '.join(failed_components)}", style="red")
                    else:
                        console.print("✅ System dependencies check passed!", style="green")
                else:
                    # Install system dependencies
                    system_success = manager.install()
                    if system_success:
                        console.print("✅ System dependencies installed!", style="green")
                    else:
                        console.print("❌ System dependency installation failed!", style="red")

            except Exception as e:
                system_success = False
                console.print(f"❌ System dependency error: {e}", style="red")

        # Final status
        overall_success = python_success and system_success

        if check_only:
            if overall_success:
                console.print("✅ All dependency checks completed successfully!", style="bold green")
            else:
                console.print("❌ Some dependency checks failed. See details above.", style="bold red")
        else:
            if overall_success:
                console.print("✅ Setup completed successfully!", style="bold green")
                console.print("💡 Run 'rxiv check-installation' to verify your setup", style="dim")
            else:
                console.print("❌ Setup completed with errors. See details above.", style="bold red")

        if not overall_success:
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n⏹️  Setup interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error during setup: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)
