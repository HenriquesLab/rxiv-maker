"""ArXiv command for rxiv-maker CLI."""

import sys
from datetime import datetime
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from rxiv_maker.engines.operations.build_manager import BuildManager
from rxiv_maker.engines.operations.prepare_arxiv import main as prepare_arxiv_main

from ...core.environment_manager import EnvironmentManager
from ...core.path_manager import PathManager, PathResolutionError

console = Console()


def _extract_author_and_year(config_path: Path) -> tuple[str, str]:
    """Extract year and first author from manuscript configuration.

    Args:
        config_path: Path to the 00_CONFIG.yml file

    Returns:
        Tuple of (year, first_author) strings
    """
    if not config_path.exists():
        return str(datetime.now().year), "Unknown"

    try:
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except (yaml.YAMLError, OSError) as e:
        console.print(f"⚠️  Warning: Could not parse config file {config_path}: {e}", style="yellow")
        return str(datetime.now().year), "Unknown"

    # Extract year from date
    year = str(datetime.now().year)  # Default fallback
    date_str = config.get("date", "")
    if date_str and isinstance(date_str, str):
        try:
            year = date_str.split("-")[0] if "-" in date_str else date_str
            # Validate year is numeric
            int(year)
        except (ValueError, IndexError):
            year = str(datetime.now().year)

    # Extract first author
    first_author = "Unknown"  # Default fallback
    authors = config.get("authors", [])
    if authors and isinstance(authors, list) and len(authors) > 0:
        author_info = authors[0]
        if isinstance(author_info, dict) and "name" in author_info:
            author_name = author_info["name"]
            if isinstance(author_name, str) and author_name.strip():
                # Extract last name (last word) from full name
                first_author = author_name.split()[-1] if " " in author_name else author_name

    return year, first_author


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
    # Determine verbosity from context object
    verbose = ctx.obj.get("verbose", False) if ctx.obj else False
    verbose = verbose or EnvironmentManager.is_verbose()

    # Use PathManager for path resolution and validation
    try:
        # Default to environment variable or fallback if not specified
        if manuscript_path is None:
            manuscript_path = EnvironmentManager.get_manuscript_path() or "MANUSCRIPT"

        # Use PathManager for path validation and resolution
        path_manager = PathManager(manuscript_path=manuscript_path, output_dir=output_dir)

    except PathResolutionError as e:
        click.secho(f"❌ Path resolution error: {e}", fg="red")
        click.secho(f"💡 Run 'rxiv init {manuscript_path}' to create a new manuscript", fg="yellow")
        sys.exit(1)

    # Set defaults using PathManager
    manuscript_output_dir = str(path_manager.output_dir)
    if arxiv_dir is None:
        arxiv_dir = str(Path(manuscript_output_dir) / "arxiv_submission")
    if zip_filename is None:
        zip_filename = str(Path(manuscript_output_dir) / "for_arxiv.zip")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            # First, ensure PDF is built
            task = progress.add_task("Checking PDF exists...", total=None)
            # Build full PDF path using PathManager
            pdf_filename = f"{path_manager.manuscript_name}.pdf"
            pdf_path = path_manager.output_dir / pdf_filename

            if not pdf_path.exists():
                progress.update(task, description="Building PDF first...")
                # Use BuildManager with PathManager paths
                build_manager = BuildManager(
                    manuscript_path=str(path_manager.manuscript_path),
                    output_dir=str(path_manager.output_dir),
                    verbose=verbose,
                )
                success = build_manager.run()
                if not success:
                    console.print(
                        "❌ PDF build failed. Cannot prepare arXiv package.",
                        style="red",
                    )
                    sys.exit(1)

            # Prepare arXiv package
            progress.update(task, description="Preparing arXiv package...")

            # Prepare arguments using PathManager
            args = [
                "--output-dir",
                manuscript_output_dir,
                "--arxiv-dir",
                arxiv_dir,
                "--manuscript-path",
                str(path_manager.manuscript_path),
            ]

            if not no_zip:
                args.extend(["--zip-filename", zip_filename, "--create-zip"])

            # Note: prepare_arxiv doesn't support --verbose flag

            # Save original argv and replace
            original_argv = sys.argv
            sys.argv = ["prepare_arxiv"] + args

            try:
                prepare_arxiv_main()
                progress.update(task, description="✅ arXiv package prepared")
                console.print("✅ arXiv package prepared successfully!", style="green")

                if not no_zip:
                    console.print(f"📦 arXiv package: {zip_filename}", style="blue")

                    # Copy to manuscript directory with proper naming
                    import shutil

                    config_path = path_manager.manuscript_path / "00_CONFIG.yml"
                    year, first_author = _extract_author_and_year(config_path)

                    # Create proper filename
                    arxiv_filename = f"{year}__{first_author}_et_al__for_arxiv.zip"
                    final_path = path_manager.manuscript_path / arxiv_filename

                    # Copy file
                    shutil.copy2(zip_filename, final_path)
                    console.print(f"📋 Copied to: {final_path}", style="green")

                console.print("📤 Upload the package to arXiv for submission", style="yellow")

            except SystemExit as e:
                progress.update(task, description="❌ arXiv preparation failed")
                if e.code != 0:
                    console.print("❌ arXiv preparation failed. See details above.", style="red")
                    sys.exit(1)

            finally:
                sys.argv = original_argv

    except KeyboardInterrupt:
        console.print("\n⏹️  arXiv preparation interrupted by user", style="yellow")
        sys.exit(1)
    except (OSError, IOError) as e:
        console.print(f"❌ File operation error during arXiv preparation: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)
    except (yaml.YAMLError, ValueError) as e:
        console.print(f"❌ Configuration error during arXiv preparation: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error during arXiv preparation: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)
