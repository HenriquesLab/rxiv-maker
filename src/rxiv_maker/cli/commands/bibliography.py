"""Bibliography commands for rxiv-maker CLI."""

import click

from ..framework import BibliographyAddCommand, BibliographyFixCommand


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
    command = BibliographyFixCommand()
    return command.run(ctx, manuscript_path=manuscript_path, dry_run=dry_run)


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
    command = BibliographyAddCommand()
    return command.run(ctx, manuscript_path=manuscript_path, dois=dois, overwrite=overwrite)
