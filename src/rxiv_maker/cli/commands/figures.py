"""Figures command for rxiv-maker CLI."""

from pathlib import Path

import click
from rich.console import Console

from ...engines.operations.generate_figures import FigureGenerator
from ...utils.unicode_safe import get_safe_icon

console = Console()


@click.command()
@click.argument("manuscript_path", required=False)
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

    MANUSCRIPT_PATH: Path to manuscript directory (default: auto-detect or current directory)

    This command generates figures from:
    - Python scripts (*.py)
    - R scripts (*.R)
    - Mermaid diagrams (*.mmd)
    """
    # Use the same path resolution logic as the build command
    if manuscript_path is None:
        # First check environment variable
        from ...core.environment_manager import EnvironmentManager

        manuscript_path = EnvironmentManager.get_manuscript_path()

        # If no environment variable, check if we're already in a manuscript directory
        if manuscript_path is None:
            from ...core.cache.cache_utils import find_manuscript_directory

            manuscript_dir = find_manuscript_directory()
            if manuscript_dir is not None:
                manuscript_path = str(manuscript_dir)
                if verbose or ctx.obj.get("verbose", False):
                    console.print(
                        f"{get_safe_icon('🔍', '[SEARCH]')} Detected manuscript directory: {manuscript_path}",
                        style="green",
                    )
            else:
                # Fall back to current directory
                manuscript_path = "."
                if verbose or ctx.obj.get("verbose", False):
                    console.print(
                        f"{get_safe_icon('📁', '[FOLDER]')} Using current directory: {manuscript_path}", style="blue"
                    )

    manuscript_dir = Path(manuscript_path).resolve()
    if not manuscript_dir.exists():
        console.print(
            f"{get_safe_icon('❌', '[ERROR]')} Manuscript directory not found: {manuscript_path}", style="red"
        )
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
                console.print(
                    f"{get_safe_icon('🎨', '[ART]')} Starting figure generation ({mode_msg})...", style="blue"
                )

            generator.process_figures()

        console.print(f"{get_safe_icon('✅', '[OK]')} Figures generated successfully!", style="green")
        console.print(f"{get_safe_icon('📁', '[FOLDER]')} Figures directory: {figures_dir}", style="blue")

    except Exception as e:
        console.print(f"{get_safe_icon('❌', '[ERROR]')} Figure generation failed: {e}", style="red")
        ctx.exit(1)
