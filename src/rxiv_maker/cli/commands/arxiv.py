"""ArXiv command for rxiv-maker CLI."""

import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


@click.command()
@click.argument(
    "manuscript_path", type=click.Path(exists=True, file_okay=False), required=False
)
@click.option(
    "--output-dir", "-o", default="output", help="Output directory for generated files"
)
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

    # Set defaults
    if arxiv_dir is None:
        arxiv_dir = str(Path(output_dir) / "arxiv_submission")
    if zip_filename is None:
        zip_filename = str(Path(output_dir) / "for_arxiv.zip")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            # First, ensure PDF is built
            task = progress.add_task("Checking PDF exists...", total=None)
            pdf_path = Path(output_dir) / f"{Path(manuscript_path).name}.pdf"

            if not pdf_path.exists():
                progress.update(task, description="Building PDF first...")
                from rxiv_maker.engine.build_manager import BuildManager

                build_manager = BuildManager(
                    manuscript_path=manuscript_path,
                    output_dir=output_dir,
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

            # Import arXiv preparation command
            from rxiv_maker.engine.prepare_arxiv import main as prepare_arxiv_main

            # Prepare arguments
            args = [
                "--output-dir",
                output_dir,
                "--arxiv-dir",
                arxiv_dir,
                "--manuscript-path",
                manuscript_path,
            ]

            if not no_zip:
                args.extend(["--zip-filename", zip_filename, "--create-zip"])

            if verbose:
                args.append("--verbose")

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
                    import yaml

                    config_path = Path(manuscript_path) / "00_CONFIG.yml"
                    if config_path.exists():
                        with open(config_path, encoding="utf-8") as f:
                            config = yaml.safe_load(f)

                        # Extract year and first author
                        year = (
                            config.get("date", "").split("-")[0]
                            if config.get("date")
                            else "2024"
                        )
                        authors = config.get("authors", [])
                        if authors:
                            first_author = (
                                authors[0]["name"].split()[-1]
                                if " " in authors[0]["name"]
                                else authors[0]["name"]
                            )
                        else:
                            first_author = "Unknown"

                        # Create proper filename
                        arxiv_filename = f"{year}__{first_author}_et_al__for_arxiv.zip"
                        final_path = Path(manuscript_path) / arxiv_filename

                        # Copy file
                        import shutil

                        shutil.copy2(zip_filename, final_path)
                        console.print(f"📋 Copied to: {final_path}", style="green")

                console.print(
                    "📤 Upload the package to arXiv for submission", style="yellow"
                )

            except SystemExit as e:
                progress.update(task, description="❌ arXiv preparation failed")
                if e.code != 0:
                    console.print(
                        "❌ arXiv preparation failed. See details above.", style="red"
                    )
                    sys.exit(1)

            finally:
                sys.argv = original_argv

    except KeyboardInterrupt:
        console.print("\n⏹️  arXiv preparation interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error during arXiv preparation: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)
