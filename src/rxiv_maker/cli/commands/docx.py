"""DOCX export command for rxiv-maker CLI."""

import rich_click as click
from rich.console import Console

from ...core.logging_config import get_logger
from ...exporters.docx_exporter import DocxExporter

logger = get_logger()
console = Console()


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument(
    "manuscript_path",
    type=click.Path(exists=True, file_okay=False),
    required=False,
    metavar="[MANUSCRIPT_PATH]",
)
@click.option(
    "--resolve-dois",
    "-r",
    is_flag=True,
    help="Attempt to resolve missing DOIs from metadata",
)
@click.option(
    "--no-footnotes",
    is_flag=True,
    help="Disable references section (citations only)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-essential output")
def docx(
    manuscript_path: str | None,
    resolve_dois: bool,
    no_footnotes: bool,
    verbose: bool,
    quiet: bool,
) -> None:
    """Export manuscript to DOCX format for collaborative review.

    Generates a Word document with numbered citations, embedded figures,
    and a complete references section with DOI links. Output is automatically
    saved to the manuscript directory with the same naming pattern as the PDF.

    **MANUSCRIPT_PATH**: Directory containing manuscript files.
    Defaults to MANUSCRIPT/

    **Output**: Automatically saved to MANUSCRIPT/YEAR__lastname_et_al__rxiv.docx

    ## Examples

    **Basic export:**

        $ rxiv docx

    **Export from custom directory:**

        $ rxiv docx MY_PAPER/

    **With DOI resolution for missing entries:**

        $ rxiv docx --resolve-dois

    **Without references section (citations only):**

        $ rxiv docx --no-footnotes
    """
    try:
        # Configure logging
        if verbose:
            logger.set_level("DEBUG")
        elif quiet:
            logger.set_level("WARNING")

        # Set manuscript path
        manuscript_path = manuscript_path or "MANUSCRIPT"

        # Create exporter
        if not quiet:
            console.print("[cyan]📄 Exporting manuscript to DOCX...[/cyan]")

        exporter = DocxExporter(
            manuscript_path=manuscript_path,
            resolve_dois=resolve_dois,
            include_footnotes=not no_footnotes,
        )

        # Perform export
        docx_path = exporter.export()

        # Success message
        if not quiet:
            console.print(f"[green]✅ DOCX exported:[/green] {docx_path}")

    except FileNotFoundError as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        raise click.Abort() from e
    except Exception as e:
        if verbose:
            logger.error(f"DOCX export failed: {e}")
        console.print(f"[red]❌ Export failed:[/red] {e}")
        raise click.Abort() from e
