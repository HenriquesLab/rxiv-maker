"""Validate command for rxiv-maker CLI."""

import rich_click as click

from ..framework import ValidationCommand


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("manuscript_path", type=click.Path(exists=True, file_okay=False), required=False)
@click.option("--detailed", "-d", is_flag=True, help="Show detailed validation report")
@click.option("--no-doi", is_flag=True, help="Skip DOI validation")
@click.pass_context
def validate(ctx: click.Context, manuscript_path: str | None, detailed: bool, no_doi: bool) -> None:
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
    # Use centralized CommandFramework - eliminates 60+ lines of boilerplate!
    command = ValidationCommand()
    command.run(ctx, manuscript_path, detailed=detailed, no_doi=no_doi)
