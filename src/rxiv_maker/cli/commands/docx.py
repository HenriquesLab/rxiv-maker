"""DOCX export command for rxiv-maker CLI."""

import platform
import shutil
import subprocess
from pathlib import Path

import rich_click as click
from rich.console import Console

from ...core.logging_config import get_logger
from ...core.managers.dependency_manager import DependencyStatus, get_dependency_manager
from ...exporters.docx_exporter import DocxExporter
from ...utils.unicode_safe import get_safe_icon

logger = get_logger()
console = Console()


def _check_and_offer_poppler_installation(console: Console, quiet: bool, verbose: bool) -> None:
    """Check poppler availability and offer automatic installation via brew.

    Args:
        console: Rich console for output
        quiet: Whether to suppress output
        verbose: Whether verbose mode is enabled
    """
    # Check if poppler is installed
    manager = get_dependency_manager()
    result = manager.check_dependency("pdftoppm")

    if result.status == DependencyStatus.AVAILABLE:
        if verbose:
            console.print("[dim]✓ Poppler utilities available[/dim]")
        return

    # Poppler is missing - offer to install
    system = platform.system()

    if system == "Darwin" and shutil.which("brew"):
        # macOS with Homebrew
        if not quiet:
            console.print("[yellow]⚠️  Poppler not found[/yellow]")
            console.print("   Poppler is needed to embed PDF figures in DOCX files.")
            console.print("   Without it, PDF figures will appear as placeholders.")
            console.print()

        if click.confirm("   Would you like to install poppler now via Homebrew?", default=True):
            console.print("[cyan]Installing poppler...[/cyan]")
            try:
                result = subprocess.run(
                    ["brew", "install", "poppler"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                if result.returncode == 0:
                    console.print("[green]✅ Poppler installed successfully![/green]")
                    # Clear dependency cache so it gets re-checked
                    manager.clear_cache()
                else:
                    console.print(f"[red]❌ Installation failed:[/red] {result.stderr}")
                    console.print("   You can install manually with: brew install poppler")
            except subprocess.TimeoutExpired:
                console.print("[red]❌ Installation timed out[/red]")
            except Exception as e:
                console.print(f"[red]❌ Installation error:[/red] {e}")
        else:
            console.print("   [dim]Skipping poppler installation. PDF figures will show as placeholders.[/dim]")

    elif system == "Linux":
        # Linux
        if not quiet:
            console.print("[yellow]⚠️  Poppler not found[/yellow]")
            console.print("   Install with: sudo apt install poppler-utils")
            console.print()
    else:
        # Other platforms or brew not available
        if not quiet:
            console.print("[yellow]⚠️  Poppler not found[/yellow]")
            console.print(f"   Install instructions: {result.resolution_hint}")
            console.print()


def _export_docx_file(
    manuscript_path: str,
    resolve_dois: bool,
    no_footnotes: bool,
    content_mode: str,
    output_suffix: str | None,
) -> Path:
    """Export one DOCX artifact and return its path."""
    exporter = DocxExporter(
        manuscript_path=manuscript_path,
        resolve_dois=resolve_dois,
        include_footnotes=not no_footnotes,
        content_mode=content_mode,
        output_suffix=output_suffix,
    )
    return exporter.export()


def _build_and_export_si_pdf(manuscript_path: str, quiet: bool, verbose: bool) -> Path:
    """Build the manuscript PDF, split SI, and copy the SI PDF beside the manuscript."""
    from ...engines.operations.build_manager import BuildManager
    from ...processors.yaml_processor import extract_yaml_metadata
    from ...utils.file_helpers import find_manuscript_md
    from ...utils.pdf_splitter import split_pdf
    from ...utils.pdf_utils import get_custom_pdf_filename

    if not quiet:
        console.print(f"[cyan]{get_safe_icon('📄', '[PDF]')} Building PDF for SI split...[/cyan]")

    build_manager = BuildManager(
        manuscript_path=manuscript_path,
        output_dir="output",
        verbose=verbose,
        quiet=quiet,
    )
    if not build_manager.build():
        raise RuntimeError("PDF build failed")

    _, si_path = split_pdf(build_manager.output_pdf)
    if si_path is None:
        raise RuntimeError("Could not split PDF: SI section marker not found")

    manuscript_dir = Path(manuscript_path)
    manuscript_md = find_manuscript_md(str(manuscript_dir))
    yaml_metadata = extract_yaml_metadata(str(manuscript_md))
    base_name = get_custom_pdf_filename(yaml_metadata).replace(".pdf", "")
    final_si_path = manuscript_dir / f"{base_name}__si.pdf"
    shutil.copy2(si_path, final_si_path)
    return final_si_path


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
@click.option("--split-si", is_flag=True, help="Split DOCX into main and SI documents (__main.docx and __si.docx)")
@click.option("--split-si-pdf", is_flag=True, help="Export main DOCX and SI PDF (__main.docx and __si.pdf)")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-essential output")
def docx(
    manuscript_path: str | None,
    resolve_dois: bool,
    no_footnotes: bool,
    split_si: bool,
    split_si_pdf: bool,
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

    **Split main and SI into separate DOCX files:**

        $ rxiv docx --split-si

    **Export main as DOCX and SI as PDF:**

        $ rxiv docx --split-si-pdf
    """
    if split_si and split_si_pdf:
        raise click.UsageError("--split-si and --split-si-pdf cannot be used together")

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

        # Pre-flight check for poppler (if manuscript contains PDF figures)
        _check_and_offer_poppler_installation(console, quiet, verbose)

        # Perform export
        if split_si:
            main_docx_path = _export_docx_file(
                manuscript_path,
                resolve_dois,
                no_footnotes,
                content_mode="main",
                output_suffix="__main",
            )
            si_docx_path = _export_docx_file(
                manuscript_path,
                resolve_dois,
                no_footnotes,
                content_mode="si",
                output_suffix="__si",
            )
            if not quiet:
                console.print("[green]✅ DOCX split successfully:[/green]")
                console.print(f"   Main: {main_docx_path}")
                console.print(f"   SI: {si_docx_path}")
            return

        if split_si_pdf:
            main_docx_path = _export_docx_file(
                manuscript_path,
                resolve_dois,
                no_footnotes,
                content_mode="main",
                output_suffix="__main",
            )
            si_pdf_path = _build_and_export_si_pdf(manuscript_path, quiet, verbose)
            if not quiet:
                console.print("[green]✅ DOCX/PDF split successfully:[/green]")
                console.print(f"   Main DOCX: {main_docx_path}")
                console.print(f"   SI PDF: {si_pdf_path}")
            return

        docx_path = _export_docx_file(
            manuscript_path,
            resolve_dois,
            no_footnotes,
            content_mode="full",
            output_suffix=None,
        )

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
