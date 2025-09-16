"""Init command for rxiv-maker CLI."""

import click

from ..framework import InitCommand


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("manuscript_path", type=click.Path(), required=False)
@click.option("--force", "-f", is_flag=True, help="Force overwrite existing files")
@click.option("--no-interactive", is_flag=True, help="Skip interactive prompts and use defaults")
@click.option(
    "--validate", is_flag=True, help="Run validation after initialization to ensure template builds correctly"
)
@click.pass_context
def init(
    ctx: click.Context,
    manuscript_path: str | None,
    force: bool,
    no_interactive: bool,
    validate: bool,
) -> None:
    """Initialize a new manuscript directory with template files and structure.

    **MANUSCRIPT_PATH**: Directory to create for your manuscript.
    Defaults to MANUSCRIPT/

    Creates all required files including configuration, main content, supplementary
    information, bibliography, and figure directory with example scripts.

    ## Examples

    **Initialize default manuscript:**

        $ rxiv init

    **Initialize custom manuscript directory:**

        $ rxiv init MY_PAPER/

    **Force overwrite existing directory:**

        $ rxiv init --force

    **Initialize and validate template builds correctly:**

        $ rxiv init --validate

    **Non-interactive initialization:**

        $ rxiv init --no-interactive
    """
    # Use centralized InitCommand framework - eliminates 250+ lines of boilerplate!
    command = InitCommand()
    command.run(ctx, manuscript_path=manuscript_path, force=force, no_interactive=no_interactive, validate=validate)
