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

            # Import bibliography fixing command
            from ...engine.fix_bibliography import main as fix_bibliography_main

            # Prepare arguments
            args = [manuscript_path]
            if dry_run:
                args.append("--dry-run")
            if verbose:
                args.append("--verbose")

            # Save original argv and replace
            original_argv = sys.argv
            sys.argv = ["fix_bibliography"] + args

            try:
                fix_bibliography_main()
                progress.update(task, description="✅ Bibliography fixes completed")
                if dry_run:
                    console.print("✅ Bibliography fixes preview completed!", style="green")
                else:
                    console.print("✅ Bibliography fixes applied successfully!", style="green")

            except SystemExit as e:
                progress.update(task, description="❌ Bibliography fixing failed")
                if e.code != 0:
                    console.print("❌ Bibliography fixing failed. See details above.", style="red")
                    sys.exit(1)

            finally:
                sys.argv = original_argv

    except KeyboardInterrupt:
        console.print("\\n⏹️  Bibliography fixing interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error during bibliography fixing: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)


@bibliography.command()
@click.argument("manuscript_path", type=click.Path(exists=True, file_okay=False), required=False)
@click.argument("dois", nargs=-1, required=True)
@click.option("--overwrite", "-o", is_flag=True, help="Overwrite existing entries")
@click.pass_context
def add(
    ctx: click.Context,
    manuscript_path: str | None,
    dois: tuple[str, ...],
    overwrite: bool,
) -> None:
    """Add bibliography entries from DOIs or URLs.

    MANUSCRIPT_PATH: Path to manuscript directory (default: MANUSCRIPT)
    DOIS: One or more DOIs or URLs containing DOIs to add

    Examples:
    rxiv bibliography add 10.1000/example.doi
    rxiv bibliography add https://www.nature.com/articles/d41586-022-00563-z
    rxiv bibliography add 10.1000/ex1 https://doi.org/10.1000/ex2
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

            # Import bibliography adding command
            from ...engine.add_bibliography import main as add_bibliography_main

            # Prepare arguments with original inputs (URLs or DOIs)
            args = [manuscript_path] + list(dois)
            if overwrite:
                args.append("--overwrite")
            if verbose:
                args.append("--verbose")

            # Save original argv and replace
            original_argv = sys.argv
            sys.argv = ["add_bibliography"] + args

            try:
                add_bibliography_main()
                progress.update(task, description="✅ Bibliography entries added")
                console.print(
                    f"✅ Added {len(dois)} bibliography entries successfully!",
                    style="green",
                )
                console.print(f"📚 Inputs processed: {', '.join(dois)}", style="blue")

            except SystemExit as e:
                progress.update(task, description="❌ Bibliography adding failed")
                if e.code != 0:
                    console.print("❌ Bibliography adding failed. See details above.", style="red")
                    sys.exit(1)

            finally:
                sys.argv = original_argv

    except KeyboardInterrupt:
        console.print("\\n⏹️  Bibliography adding interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error during bibliography adding: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)


@bibliography.command()
@click.argument("manuscript_path", type=click.Path(exists=True, file_okay=False), required=False)
@click.option("--no-doi", is_flag=True, help="Skip DOI validation")
@click.pass_context
def validate(ctx: click.Context, manuscript_path: str | None, no_doi: bool) -> None:
    """Validate bibliography entries.

    MANUSCRIPT_PATH: Path to manuscript directory (default: MANUSCRIPT)

    This command validates bibliography entries for:
    - Correct format
    - DOI validity
    - Required fields
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
            task = progress.add_task("Validating bibliography...", total=None)

            # Import validation command (we'll use the main validate command)
            from ...engine.validate import main as validate_main

            # Prepare arguments
            args = [manuscript_path]
            if no_doi:
                args.append("--no-doi")
            if verbose:
                args.append("--verbose")

            # Save original argv and replace
            original_argv = sys.argv
            sys.argv = ["validate"] + args

            try:
                validate_main()
                progress.update(task, description="✅ Bibliography validation completed")
                console.print("✅ Bibliography validation passed!", style="green")

            except SystemExit as e:
                progress.update(task, description="❌ Bibliography validation failed")
                if e.code != 0:
                    console.print(
                        "❌ Bibliography validation failed. See details above.",
                        style="red",
                    )
                    sys.exit(1)

            finally:
                sys.argv = original_argv

    except KeyboardInterrupt:
        console.print("\\n⏹️  Bibliography validation interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error during bibliography validation: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)
