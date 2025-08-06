"""PDF command for rxiv-maker CLI."""

import os
import sys
from pathlib import Path

import rich_click as click
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...core.logging_config import get_logger, set_debug, set_log_directory, set_quiet
from ...engine.build_manager import BuildManager

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

    # Use local verbose flag if provided, otherwise fall back to global context
    verbose = verbose or ctx.obj.get("verbose", False)
    engine = ctx.obj.get("engine", "local")

    # Default to MANUSCRIPT if not specified
    if manuscript_path is None:
        manuscript_path = os.environ.get("MANUSCRIPT_PATH", "MANUSCRIPT")

    # Set up preliminary log directory (will be updated by BuildManager)
    manuscript_dir = Path(manuscript_path)
    if Path(output_dir).is_absolute():
        preliminary_output_dir = Path(output_dir)
    else:
        preliminary_output_dir = manuscript_dir / output_dir

    # Set up logging to the output directory early
    set_log_directory(preliminary_output_dir)

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

    # Validate manuscript path exists
    if not Path(manuscript_path).exists():
        logger.error(f"Manuscript directory '{manuscript_path}' does not exist")
        logger.tip(f"Run 'rxiv init {manuscript_path}' to create a new manuscript")
        from ...core.logging_config import cleanup

        cleanup()
        sys.exit(1)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=logger.console,
            transient=True,
        ) as progress:
            # Create build manager
            task = progress.add_task("Initializing build manager...", total=None)
            build_manager = BuildManager(
                manuscript_path=manuscript_path,
                output_dir=output_dir,
                force_figures=force_figures,
                skip_validation=skip_validation,
                track_changes_tag=track_changes,
                verbose=verbose,
                engine=engine,
            )

            # Build the PDF
            progress.update(task, description="Generating PDF...")
            success = build_manager.run_full_build()

            if success:
                progress.update(task, description="✅ PDF generated successfully!")
                logger.success(f"PDF generated: {output_dir}/{Path(manuscript_path).name}.pdf")

                # Show additional info
                if track_changes:
                    logger.info(f"Change tracking enabled against tag: {track_changes}")
                if force_figures:
                    logger.info("All figures regenerated")

            else:
                progress.update(task, description="❌ PDF generation failed")
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
