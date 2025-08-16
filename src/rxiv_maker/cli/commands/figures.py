"""Figures command for rxiv-maker CLI."""

import click

from ..framework import FiguresCommand


@click.command()
@click.argument("manuscript_path", type=click.Path(exists=True, file_okay=False), required=False)
@click.option("--force", "-f", is_flag=True, help="Force regeneration of all figures")
@click.option("--figures-dir", "-d", help="Custom figures directory path")
@click.pass_context
def figures(
    ctx: click.Context,
    manuscript_path: str | None,
    force: bool,
    figures_dir: str | None,
) -> None:
    """Generate figures from scripts.

    MANUSCRIPT_PATH: Path to manuscript directory (default: MANUSCRIPT)

    This command generates figures from:
    - Python scripts (*.py)
    - R scripts (*.R)
    - Mermaid diagrams (*.mmd)
    """
    # Use centralized CommandFramework - eliminates 130+ lines of boilerplate!
    command = FiguresCommand()
    command.run(ctx, manuscript_path, force=force, figures_dir=figures_dir)
