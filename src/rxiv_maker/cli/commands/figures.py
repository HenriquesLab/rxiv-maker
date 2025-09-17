"""Figures command for rxiv-maker CLI."""

from pathlib import Path

import click
from rich.console import Console

from ...engines.operations.generate_figures import FigureGenerator

console = Console()


@click.command()
@click.argument("manuscript_path", type=click.Path(exists=True, file_okay=False), required=False)
@click.option("--force", "-f", is_flag=True, help="Force regeneration of all figures")
@click.option("--figures-dir", "-d", help="Custom figures directory path")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def figures(
    ctx: click.Context,
    manuscript_path: str | None,
    force: bool,
    figures_dir: str | None,
    verbose: bool,
) -> None:
    """Generate figures from scripts.

    MANUSCRIPT_PATH: Path to manuscript directory (default: MANUSCRIPT)

    This command generates figures from:
    - Python scripts (*.py)
    - R scripts (*.R)
    - Mermaid diagrams (*.mmd)
    """
    # Direct figure generation - no framework overhead!
    if manuscript_path is None:
        manuscript_path = "MANUSCRIPT"

    manuscript_dir = Path(manuscript_path)
    if not manuscript_dir.exists():
        console.print(f"❌ Manuscript directory not found: {manuscript_path}", style="red")
        ctx.exit(1)

    # Set figures directory
    if figures_dir is None:
        figures_dir = str(manuscript_dir / "FIGURES")

    try:
        with console.status("[blue]Generating figures..."):
            generator = FigureGenerator(
                figures_dir=figures_dir,
                output_dir=figures_dir,
                output_format="pdf",
                r_only=False,
                enable_content_caching=not force,
                manuscript_path=str(manuscript_dir),
            )

            if verbose or ctx.obj.get("verbose", False):
                mode_msg = "force mode - ignoring cache" if force else "normal mode"
                console.print(f"🎨 Starting figure generation ({mode_msg})...", style="blue")

            generator.process_figures()

        console.print("✅ Figures generated successfully!", style="green")
        console.print(f"📁 Figures directory: {figures_dir}", style="blue")

    except Exception as e:
        console.print(f"❌ Figure generation failed: {e}", style="red")
        ctx.exit(1)
