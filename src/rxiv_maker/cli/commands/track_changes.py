"""Track changes command for rxiv-maker CLI."""

import click

from ..framework import TrackChangesCommand


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
    command = TrackChangesCommand()
    return command.run(
        ctx,
        manuscript_path=manuscript_path,
        tag=tag,
        output_dir=output_dir,
        force_figures=force_figures,
        skip_validation=skip_validation,
    )
