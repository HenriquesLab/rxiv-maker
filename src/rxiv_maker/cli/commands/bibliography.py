"""Bibliography commands for rxiv-maker CLI."""

import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


@click.group()
def bibliography():
    """Bibliography management commands."""
    pass


@bibliography.command()
@click.argument("manuscript_path", type=click.Path(exists=True, file_okay=False), required=False)
@click.option("--dry-run", "-d", is_flag=True, help="Preview fixes without applying them")
@click.pass_context
def fix(ctx: click.Context, manuscript_path: str | None, dry_run: bool) -> None:
    """Fix bibliography issues automatically.

    MANUSCRIPT_PATH: Path to manuscript directory (default: MANUSCRIPT)

    This command searches CrossRef to fix bibliography issues.
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
        sys.exit(1)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Fixing bibliography...", total=None)

            # Import bibliography fixing class directly
            from ...engines.operations.fix_bibliography import BibliographyFixer

            try:
                # Create and use the BibliographyFixer class directly
                fixer = BibliographyFixer(manuscript_path)
                result = fixer.fix_bibliography(dry_run=dry_run)

                success = result.get("total_fixes", 0) >= 0  # Consider any result a success

                if success:
                    progress.update(task, description="✅ Bibliography fixes completed")
                    if dry_run:
                        console.print("✅ Bibliography fixes preview completed!", style="green")
                        if result.get("total_fixes", 0) > 0:
                            console.print(f"📝 Found {result['total_fixes']} potential fixes", style="blue")
                    else:
                        console.print("✅ Bibliography fixes applied successfully!", style="green")
                        if result.get("total_fixes", 0) > 0:
                            console.print(f"🔧 Applied {result['total_fixes']} fixes", style="blue")
                else:
                    progress.update(task, description="❌ Bibliography fixing failed")
                    console.print("❌ Bibliography fixing failed. See details above.", style="red")
                    sys.exit(1)

            except Exception as e:
                progress.update(task, description="❌ Bibliography fixing failed")
                console.print(f"❌ Bibliography fixing failed: {e}", style="red")
                if verbose:
                    console.print_exception()
                sys.exit(1)

    except KeyboardInterrupt:
        console.print("\\n⏹️  Bibliography fixing interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error during bibliography fixing: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)


@bibliography.command()
@click.argument("dois", nargs=-1, required=True)
@click.option(
    "--manuscript-path",
    "-m",
    type=click.Path(exists=True, file_okay=False),
    help="Path to manuscript directory (default: MANUSCRIPT)",
)
@click.option("--overwrite", "-o", is_flag=True, help="Overwrite existing entries")
@click.pass_context
def add(
    ctx: click.Context,
    dois: tuple[str, ...],
    manuscript_path: str | None,
    overwrite: bool,
) -> None:
    """Add bibliography entries from DOIs or URLs.

    DOIS: One or more DOIs or URLs containing DOIs to add

    Examples:
    rxiv bibliography add 10.1000/example.doi
    rxiv bibliography add https://www.nature.com/articles/d41586-022-00563-z
    rxiv bibliography add 10.1000/ex1 https://doi.org/10.1000/ex2
    rxiv bibliography add --manuscript-path MY_PAPER/ 10.1000/example.doi
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
        sys.exit(1)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Adding {len(dois)} bibliography entries...", total=None)

            # Import bibliography adding class directly
            from ...engines.operations.add_bibliography import BibliographyAdder

            try:
                # Create and use the BibliographyAdder class directly
                adder = BibliographyAdder(manuscript_path, overwrite=overwrite)

                # Add each DOI/URL
                total_added = 0
                for doi in dois:
                    try:
                        if adder.add_entry_from_input(doi):
                            total_added += 1
                            if verbose:
                                console.print(f"✅ Added entry for: {doi}", style="green")
                    except Exception as e:
                        console.print(f"⚠️  Failed to add {doi}: {e}", style="yellow")
                        if verbose:
                            console.print_exception()

                if total_added > 0:
                    progress.update(task, description="✅ Bibliography entries added")
                    console.print(
                        f"✅ Added {total_added} out of {len(dois)} bibliography entries successfully!",
                        style="green",
                    )
                    console.print(f"📚 Inputs processed: {', '.join(dois)}", style="blue")
                else:
                    progress.update(task, description="❌ No entries were added")
                    console.print("❌ No bibliography entries could be added. See details above.", style="red")
                    sys.exit(1)

            except Exception as e:
                progress.update(task, description="❌ Bibliography adding failed")
                console.print(f"❌ Bibliography adding failed: {e}", style="red")
                if verbose:
                    console.print_exception()
                sys.exit(1)

    except KeyboardInterrupt:
        console.print("\\n⏹️  Bibliography adding interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error during bibliography adding: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)


# Note: 'rxiv bibliography validate' command removed in favor of unified 'rxiv validate'
# The main validate command now handles bibliography validation as part of comprehensive checks
