"""Clean command for rxiv-maker CLI."""

import os
import sys

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


@click.command()
@click.argument("manuscript_path", type=click.Path(exists=True, file_okay=False), required=False)
@click.option("--output-dir", "-o", default="output", help="Output directory to clean")
@click.option("--figures-only", "-f", is_flag=True, help="Clean only generated figures")
@click.option("--output-only", "-O", is_flag=True, help="Clean only output directory")
@click.option("--arxiv-only", "-a", is_flag=True, help="Clean only arXiv files")
@click.option("--temp-only", "-t", is_flag=True, help="Clean only temporary files")
@click.option("--cache-only", "-c", is_flag=True, help="Clean only cache files")
@click.option("--all", "-A", is_flag=True, help="Clean all generated files")
@click.pass_context
def clean(
    ctx: click.Context,
    manuscript_path: str | None,
    output_dir: str,
    figures_only: bool,
    output_only: bool,
    arxiv_only: bool,
    temp_only: bool,
    cache_only: bool,
    all: bool,
) -> None:
    """Clean generated files and directories.

    MANUSCRIPT_PATH: Path to manuscript directory (default: MANUSCRIPT)

    This command removes:
    - Generated PDF files
    - Temporary LaTeX files
    - Generated figures
    - Cache files
    - arXiv submission packages
    """
    verbose = ctx.obj.get("verbose", False)

    # Default to MANUSCRIPT if not specified
    if manuscript_path is None:
        manuscript_path = os.environ.get("MANUSCRIPT_PATH", "MANUSCRIPT")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Cleaning files...", total=None)

            # Import cleanup command
            from ...engine.cleanup import main as cleanup_main

            # Prepare arguments
            args = []
            if figures_only:
                args.append("--figures-only")
            if output_only:
                args.append("--output-only")
            if arxiv_only:
                args.append("--arxiv-only")
            if temp_only:
                args.append("--temp-only")
            if cache_only:
                args.append("--cache-only")
            if verbose:
                args.append("--verbose")

            # Add paths
            args.extend(["--manuscript-path", manuscript_path])
            args.extend(["--output-dir", output_dir])

            # Save original argv and replace
            original_argv = sys.argv
            sys.argv = ["cleanup"] + args

            try:
                cleanup_main()
                progress.update(task, description="✅ Cleanup completed")
                console.print("✅ Cleanup completed!", style="green")

                # Show what was cleaned
                if figures_only:
                    console.print("🎨 Generated figures cleaned", style="blue")
                elif output_only:
                    console.print("📁 Output directory cleaned", style="blue")
                elif arxiv_only:
                    console.print("📦 arXiv files cleaned", style="blue")
                elif temp_only:
                    console.print("🧹 Temporary files cleaned", style="blue")
                elif cache_only:
                    console.print("💾 Cache files cleaned", style="blue")
                else:
                    console.print("🧹 All generated files cleaned", style="blue")

            except SystemExit as e:
                progress.update(task, description="❌ Cleanup failed")
                if e.code != 0:
                    console.print("❌ Cleanup failed. See details above.", style="red")
                    sys.exit(1)

            finally:
                sys.argv = original_argv

    except KeyboardInterrupt:
        console.print("\n⏹️  Cleanup interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error during cleanup: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)
