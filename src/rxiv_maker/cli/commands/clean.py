"""Clean command for rxiv-maker CLI."""

import click

from ...engines.operations.cleanup import CleanupManager


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("manuscript_path", type=click.Path(exists=True, file_okay=False), required=False)
@click.option("--output-dir", "-o", default="output", help="Output directory to clean")
@click.option("--figures-only", "-f", is_flag=True, help="Clean only generated figures")
@click.option("--output-only", "-O", is_flag=True, help="Clean only output directory")
@click.option("--arxiv-only", "-a", is_flag=True, help="Clean only arXiv files")
@click.option("--temp-only", "-t", is_flag=True, help="Clean only temporary files")
@click.option("--cache-only", "-c", is_flag=True, help="Clean only cache files")
@click.option("--all", "-A", is_flag=True, help="Clean all generated files")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
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
    all: bool,
    verbose: bool,
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
    """
    # Direct call - no framework overhead!
    cleanup_manager = CleanupManager(
        manuscript_path=manuscript_path,
        output_dir=output_dir,
        verbose=verbose or ctx.obj.get("verbose", False),
    )

    try:
        if all:
            cleanup_manager.run_full_cleanup()
        elif figures_only:
            cleanup_manager.clean_generated_figures()
        elif output_only:
            cleanup_manager.clean_output_directory()
        elif arxiv_only:
            cleanup_manager.clean_arxiv_files()
        elif temp_only:
            cleanup_manager.clean_temporary_files()
        elif cache_only:
            cleanup_manager.clean_cache_files()
        else:
            cleanup_manager.run_full_cleanup()
    except Exception as e:
        click.echo(f"❌ Cleanup failed: {e}", err=True)
        ctx.exit(1)
