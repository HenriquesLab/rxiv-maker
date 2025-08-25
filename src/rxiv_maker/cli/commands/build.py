"""PDF command for rxiv-maker CLI."""

import sys

import rich_click as click
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...core.environment_manager import EnvironmentManager
from ...core.logging_config import get_logger, set_debug, set_log_directory, set_quiet
from ...core.path_manager import PathManager, PathResolutionError
from ...engines.operations.build_manager import BuildManager

logger = get_logger()


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument(
    "manuscript_path",
    type=click.Path(exists=True, file_okay=False),
    required=False,
    metavar="[MANUSCRIPT_PATH]",
)
@click.option(
    "--output-dir",
    "-o",
    default="output",
    help="Output directory for generated files",
    metavar="DIR",
)
@click.option("--force-figures", "-f", is_flag=True, help="Force regeneration of all figures")
@click.option("--skip-validation", "-s", is_flag=True, help="Skip validation step")
@click.option(
    "--track-changes",
    "-t",
    help="Track changes against specified git tag",
    metavar="TAG",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-essential output")
@click.option("--debug", "-d", is_flag=True, help="Enable debug output")
@click.option(
    "--container-mode",
    type=click.Choice(["reuse", "minimal", "isolated"]),
    help="Container behavior mode (reuse=max reuse, minimal=low resources, isolated=fresh containers)",
)
@click.pass_context
def build(
    ctx: click.Context,
    manuscript_path: str | None,
    output_dir: str,
    force_figures: bool,
    skip_validation: bool,
    track_changes: str | None,
    verbose: bool,
    quiet: bool,
    debug: bool,
    container_mode: str | None,
) -> None:
    """Generate a publication-ready PDF from your Markdown manuscript.

    Automated figure generation, professional typesetting, and bibliography management.

    **MANUSCRIPT_PATH**: Directory containing your manuscript files.
    Defaults to MANUSCRIPT/

    ## Examples

    **Build from default directory:**

        $ rxiv pdf

    **Build from custom directory:**

        $ rxiv pdf MY_PAPER/

    **Force regenerate all figures:**

        $ rxiv pdf --force-figures

    **Skip validation for debugging:**

        $ rxiv pdf --skip-validation

    **Track changes against git tag:**

        $ rxiv pdf --track-changes v1.0.0
    """
    # Configure logging based on flags
    if debug:
        set_debug(True)
    elif quiet:
        set_quiet(True)

    # Use local verbose flag if provided, otherwise fall back to global context and environment
    verbose = verbose or ctx.obj.get("verbose", False) or EnvironmentManager.is_verbose()
    engine = ctx.obj.get("engine") or EnvironmentManager.get_rxiv_engine()

    # Set container mode if specified (for container engines)
    if container_mode and engine in ["docker", "podman"]:
        import os

        os.environ["RXIV_CONTAINER_MODE"] = container_mode
        if verbose:
            click.echo(f"🐳 Container mode set to: {container_mode}")

    # Validate and resolve manuscript path using PathManager
    try:
        # Default to environment variable or fallback if not specified
        if manuscript_path is None:
            manuscript_path = EnvironmentManager.get_manuscript_path() or "MANUSCRIPT"

        # Use PathManager for path validation and resolution
        path_manager = PathManager(manuscript_path=manuscript_path, output_dir=output_dir)

        # Set up logging to the output directory early using PathManager
        set_log_directory(path_manager.output_dir)

        logger.debug(f"Using PathManager: manuscript={path_manager.manuscript_path}, output={path_manager.output_dir}")

    except PathResolutionError as e:
        logger.error(f"Path resolution error: {e}")
        logger.tip(f"Run 'rxiv init {manuscript_path}' to create a new manuscript")
        from ...core.logging_config import cleanup

        cleanup()
        sys.exit(1)

    # Docker engine optimization: verify Docker readiness for build pipeline
    if engine == "docker":
        from ...docker.manager import get_docker_manager

        try:
            docker_manager = get_docker_manager()
            if not docker_manager.check_docker_available():
                logger.error("Docker is not available for build pipeline. Please ensure Docker is running.")
                logger.tip("Use --engine local to build without Docker")
                from ...core.logging_config import cleanup

                cleanup()
                sys.exit(1)

            if verbose:
                logger.docker_info("Build pipeline will use Docker containers")

        except Exception as e:
            logger.error(f"Docker setup error: {e}")
            from ...core.logging_config import cleanup

            cleanup()
            sys.exit(1)

    try:
        from rich.progress import BarColumn, MofNCompleteColumn, TaskProgressColumn, TimeElapsedColumn

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=logger.console,
            transient=True,
        ) as progress:
            # Create build manager with PathManager
            initialization_task = progress.add_task("Initializing build manager...", total=None)
            build_manager = BuildManager(
                manuscript_path=manuscript_path,  # Pass original path, not resolved path
                output_dir=output_dir,  # Pass original relative path
                force_figures=force_figures,
                skip_validation=skip_validation,
                track_changes_tag=track_changes,
                verbose=verbose,
                engine=engine,
            )
            progress.update(initialization_task, description="✅ Build manager initialized")

            # Enhanced progress tracking for build steps
            build_steps = [
                "Checking manuscript structure",
                "Setting up output directory",
                "Generating figures",
                "Validating manuscript",
                "Copying style files",
                "Copying references",
                "Copying figures",
                "Generating LaTeX files",
                "Compiling PDF",
                "Finalizing build",
            ]

            # Skip validation step if requested
            if skip_validation:
                build_steps.remove("Validating manuscript")

            main_task = progress.add_task("Building PDF...", total=len(build_steps))

            # Pass progress callback to build manager
            def progress_callback(step_name, completed_steps, total_steps):
                progress.update(main_task, completed=completed_steps, description=f"📄 {step_name}")

            # Build the PDF with progress tracking
            success = build_manager.run_full_build(progress_callback=progress_callback)

            if success:
                progress.update(main_task, completed=len(build_steps), description="✅ PDF generated successfully!")
                logger.success(f"PDF generated: {path_manager.output_dir}/{path_manager.manuscript_name}.pdf")

                # Show additional info
                if track_changes:
                    logger.info(f"Change tracking enabled against tag: {track_changes}")
                if force_figures:
                    logger.info("All figures regenerated")

            else:
                progress.update(main_task, description="❌ PDF generation failed")
                logger.error("PDF generation failed. Check output above for errors.")
                logger.tip("Run with --verbose for more details")
                logger.tip("Run 'rxiv validate' to check for issues")
                from ...core.logging_config import cleanup

                cleanup()
                sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("\nPDF generation interrupted by user")
        from ...core.logging_config import cleanup

        cleanup()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if verbose:
            logger.console.print_exception()
        from ...core.logging_config import cleanup

        cleanup()
        sys.exit(1)
    finally:
        # Ensure logging cleanup for Windows compatibility
        from ...core.logging_config import cleanup

        cleanup()
