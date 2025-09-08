"""ArXiv command for rxiv-maker CLI."""

import click

from ..framework import ArxivCommand


@click.command()
@click.argument("manuscript_path", type=click.Path(file_okay=False), required=False)
@click.option("--output-dir", "-o", default="output", help="Output directory for generated files")
@click.option("--arxiv-dir", "-a", help="Custom arXiv directory path")
@click.option("--zip-filename", "-z", help="Custom zip filename")
@click.option("--no-zip", is_flag=True, help="Don't create zip file")
@click.pass_context
def arxiv(
    ctx: click.Context,
    manuscript_path: str | None,
    output_dir: str,
    arxiv_dir: str | None,
    zip_filename: str | None,
    no_zip: bool,
) -> None:
    """Prepare arXiv submission package.

    MANUSCRIPT_PATH: Path to manuscript directory (default: MANUSCRIPT)

    This command:
    1. Builds the PDF if not already built
    2. Prepares arXiv submission files
    3. Creates a zip package for upload
    4. Copies the package to the manuscript directory
    """
    command = ArxivCommand()
    return command.run(
        ctx,
        manuscript_path=manuscript_path,
        output_dir=output_dir,
        arxiv_dir=arxiv_dir,
        zip_filename=zip_filename,
        no_zip=no_zip,
    )
