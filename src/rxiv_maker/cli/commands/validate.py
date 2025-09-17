"""Validate command for rxiv-maker CLI."""

from pathlib import Path

import rich_click as click
from rich.console import Console

from ...engines.operations.validate import validate_manuscript

console = Console()


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("manuscript_path", type=click.Path(exists=True, file_okay=False), required=False)
@click.option("--detailed", "-d", is_flag=True, help="Show detailed validation report")
@click.option("--no-doi", is_flag=True, help="Skip DOI validation")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def validate(ctx: click.Context, manuscript_path: str | None, detailed: bool, no_doi: bool, verbose: bool) -> None:
    """Validate manuscript structure and content before PDF generation.

    **MANUSCRIPT_PATH**: Directory containing your manuscript files.
    Defaults to MANUSCRIPT/

    This command checks manuscript structure, citations, cross-references,
    figures, mathematical expressions, and special Markdown syntax elements.

    ## Examples

    **Validate default manuscript:**

        $ rxiv validate

    **Validate custom manuscript directory:**

        $ rxiv validate MY_PAPER/

    **Show detailed validation report:**

        $ rxiv validate --detailed

    **Skip DOI validation:**

        $ rxiv validate --no-doi
    """
    # Direct validation call - no framework overhead!
    if manuscript_path is None:
        import os

        manuscript_path = os.environ.get("MANUSCRIPT_PATH", "MANUSCRIPT")

    manuscript_dir = Path(manuscript_path)
    if not manuscript_dir.exists():
        console.print(f"❌ Manuscript directory not found: {manuscript_path}", style="red")
        ctx.exit(1)

    try:
        with console.status("[blue]Running validation..."):
            validation_passed = validate_manuscript(
                manuscript_path=str(manuscript_dir),
                detailed=detailed,
                verbose=verbose or ctx.obj.get("verbose", False),
                include_info=False,
                check_latex=True,
                enable_doi_validation=None if not no_doi else False,
            )

        if validation_passed:
            console.print("✅ Validation passed!", style="green")
        else:
            console.print("❌ Validation failed - see errors above", style="red")
            ctx.exit(1)

    except Exception as e:
        console.print(f"❌ Validation error: {e}", style="red")
        ctx.exit(1)
