"""Track changes command for rxiv-maker CLI."""

import sys

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...core.environment_manager import EnvironmentManager
from ...core.path_manager import PathManager, PathResolutionError
from ...engines.operations.build_manager import BuildManager

console = Console()


@click.command()
@click.argument("manuscript_path", type=click.Path(exists=True, file_okay=False), required=False)
@click.argument("tag", required=True)
@click.option("--output-dir", "-o", default="output", help="Output directory for generated files")
@click.option("--force-figures", "-f", is_flag=True, help="Force regeneration of all figures")
@click.option("--skip-validation", "-s", is_flag=True, help="Skip validation step")
@click.pass_context
def track_changes(
    ctx: click.Context,
    manuscript_path: str | None,
    tag: str,
    output_dir: str,
    force_figures: bool,
    skip_validation: bool,
) -> None:
    """Generate PDF with change tracking against a git tag.

    MANUSCRIPT_PATH: Path to manuscript directory (default: MANUSCRIPT)
    TAG: Git tag to track changes against
    """
    verbose = ctx.obj.get("verbose", False) or EnvironmentManager.is_verbose()

    # Use PathManager for path resolution and validation
    try:
        # Default to environment variable or fallback if not specified
        if manuscript_path is None:
            manuscript_path = EnvironmentManager.get_manuscript_path() or "MANUSCRIPT"

        # Use PathManager for path validation and resolution
        path_manager = PathManager(manuscript_path=manuscript_path, output_dir=output_dir)

    except PathResolutionError as e:
        console.print(f"❌ Path resolution error: {e}", style="red")
        console.print(f"💡 Run 'rxiv init {manuscript_path}' to create a new manuscript", style="yellow")
        sys.exit(1)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            # Create build manager with track changes enabled using PathManager
            task = progress.add_task("Initializing change tracking build...", total=None)
            build_manager = BuildManager(
                manuscript_path=str(path_manager.manuscript_path),
                output_dir=str(path_manager.output_dir),
                force_figures=force_figures,
                skip_validation=skip_validation,
                track_changes_tag=tag,
                verbose=verbose,
            )

            # Build the PDF with change tracking
            progress.update(
                task,
                description=f"Generating PDF with changes tracked against {tag}...",
            )
            success = build_manager.run_full_build()

            if success:
                progress.update(task, description="✅ Change-tracked PDF generated successfully!")
                console.print(
                    f"📄 PDF with change tracking generated: {path_manager.output_dir}/{path_manager.manuscript_name}.pdf",
                    style="green",
                )
                console.print(
                    f"🔍 Changes tracked against git tag: {tag}",
                    style="blue",
                )
            else:
                progress.update(task, description="❌ Failed to generate PDF with change tracking")
                console.print("❌ PDF generation with change tracking failed", style="red")
                sys.exit(1)

    except Exception as e:
        console.print(f"❌ Error during change tracking build: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)
