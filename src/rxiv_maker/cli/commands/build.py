"""PDF command for rxiv-maker CLI."""

import rich_click as click

from ..framework import BuildCommand


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
@click.option("--keep-output", is_flag=True, help="Preserve existing output directory (default: clear before build)")
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
    keep_output: bool,
    verbose: bool,
    quiet: bool,
    debug: bool,
    container_mode: str | None,
) -> None:
    """Generate a publication-ready PDF from your Markdown manuscript.

    Automated figure generation, professional typesetting, and bibliography management.

    By default, clears the output directory before building to ensure clean builds.

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

    **Keep existing output directory:**

        $ rxiv pdf --keep-output

    **Track changes against git tag:**

        $ rxiv pdf --track-changes v1.0.0
    """
    command = BuildCommand()
    return command.run(
        ctx,
        manuscript_path=manuscript_path,
        output_dir=output_dir,
        force_figures=force_figures,
        skip_validation=skip_validation,
        track_changes=track_changes,
        keep_output=keep_output,
        debug=debug or verbose,
        quiet=quiet,
        container_mode=container_mode,
    )
