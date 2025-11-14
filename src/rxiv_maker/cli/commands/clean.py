"""Clean command for rxiv-maker CLI."""

import click

from ..framework import CleanCommand


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("manuscript_path", type=click.Path(exists=True, file_okay=False), required=False)
@click.option("--output-dir", "-o", default="output", help="Output directory to clean")
@click.option("--figures-only", "-f", is_flag=True, help="Clean only generated figures")
@click.option("--output-only", "-O", is_flag=True, help="Clean only output directory")
@click.option("--arxiv-only", "-a", is_flag=True, help="Clean only arXiv files")
@click.option("--temp-only", "-t", is_flag=True, help="Clean only temporary files")
@click.option("--cache-only", "-c", is_flag=True, help="Clean only cache files")
@click.option("--all", "all_files", is_flag=True, help="Clean all generated files")
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode - select what to clean")
@click.pass_context
def clean(
    ctx: click.Context,
    manuscript_path: str | None,
    output_dir: str,
    figures_only: bool,
    output_only: bool,
    arxiv_only: bool,
    temp_only: bool,
    cache_only: bool,
    all_files: bool,
    interactive: bool,
) -> None:
    """Clean generated files and directories.

    **MANUSCRIPT_PATH**: Path to manuscript directory (default: MANUSCRIPT)

    This command removes:
    - Generated PDF files
    - Temporary LaTeX files
    - Generated figures
    - Cache files
    - arXiv submission packages

    ## Examples

    **Clean all generated files:**

        $ rxiv clean

    **Clean only figures:**

        $ rxiv clean --figures-only

    **Clean specific manuscript:**

        $ rxiv clean MY_PAPER/

    **Interactive mode (select what to clean):**

        $ rxiv clean --interactive
    """
    command = CleanCommand()
    return command.run(
        ctx,
        manuscript_path=manuscript_path,
        output_dir=output_dir,
        figures_only=figures_only,
        output_only=output_only,
        arxiv_only=arxiv_only,
        temp_only=temp_only,
        cache_only=cache_only,
        all_files=all_files,
        interactive=interactive,
    )
