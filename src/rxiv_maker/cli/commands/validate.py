"""Validate command for rxiv-maker CLI."""

import os
import sys
from pathlib import Path

import rich_click as click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


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
    verbose = ctx.obj.get("verbose", False)

    # Default to MANUSCRIPT if not specified
    if manuscript_path is None:
        manuscript_path = os.environ.get("MANUSCRIPT_PATH", "MANUSCRIPT")

    # Validate manuscript path exists
    if not Path(manuscript_path).exists():
        console.print(
            f"❌ Error: Manuscript directory '{manuscript_path}' does not exist",
            style="red",
        )
        console.print(
            f"💡 Run 'rxiv init {manuscript_path}' to create a new manuscript",
            style="yellow",
        )
        sys.exit(1)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Running validation...", total=None)

            # Import and run validation directly
            from ...engine.validate import validate_manuscript

            # Determine DOI validation setting: CLI flag overrides config
            enable_doi_validation = None if not no_doi else False

            # Run validation directly
            validation_passed = validate_manuscript(
                manuscript_path=manuscript_path,
                detailed=detailed,
                verbose=verbose,
                include_info=False,  # Don't include info messages in CLI output
                check_latex=True,  # Always check LaTeX by default
                enable_doi_validation=enable_doi_validation,
            )

            if validation_passed:
                progress.update(task, description="✅ Validation completed")
                console.print("✅ Validation passed!", style="green")
            else:
                progress.update(task, description="❌ Validation failed")
                console.print("❌ Validation failed. See details above.", style="red")
                console.print("💡 Run with --detailed for more information", style="yellow")
                console.print(
                    "💡 Use 'rxiv pdf --skip-validation' to build anyway",
                    style="yellow",
                )
                sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n⏹️  Validation interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error during validation: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)
