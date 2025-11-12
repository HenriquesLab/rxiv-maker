"""Main CLI entry point for rxiv-maker."""
# ruff: noqa: D301

import os

import rich_click as click
from rich.console import Console

from .. import __version__
from ..utils.update_checker import check_for_updates_async, show_update_notification
from . import commands
from .commands.check_installation import check_installation

# Configure rich-click for better help formatting
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.USE_MARKDOWN = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.SHOW_METAVARS_COLUMN = False
click.rich_click.APPEND_METAVARS_HELP = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "magenta italic"
click.rich_click.STYLE_METAVAR = "bold yellow"
click.rich_click.STYLE_OPTION = "bold green"
click.rich_click.STYLE_ARGUMENT = "bold blue"
click.rich_click.STYLE_COMMAND = "bold cyan"
click.rich_click.STYLE_SWITCH = "bold magenta"
click.rich_click.STYLE_HELPTEXT = ""
click.rich_click.STYLE_USAGE = "yellow"
click.rich_click.STYLE_USAGE_COMMAND = "bold"
click.rich_click.STYLE_HELP_HEADER = "bold blue"
click.rich_click.STYLE_FOOTER_TEXT = "dim"
click.rich_click.MAX_WIDTH = 100
click.rich_click.HEADER_TEXT = None
click.rich_click.FOOTER_TEXT = None
click.rich_click.STYLE_COMMANDS_TABLE_SHOW_LINES = False
click.rich_click.STYLE_COMMANDS_TABLE_PADDING = (0, 1)
click.rich_click.STYLE_COMMANDS_TABLE_BOX = "SIMPLE"
click.rich_click.STYLE_OPTIONS_TABLE_SHOW_LINES = False
click.rich_click.STYLE_OPTIONS_TABLE_PADDING = (0, 1)
click.rich_click.STYLE_OPTIONS_TABLE_BOX = "SIMPLE"
click.rich_click.STYLE_COMMANDS_TABLE_COLUMN_WIDTH_RATIO = (1, 2)
click.rich_click.COMMAND_GROUPS = {
    "rxiv": [
        {
            "name": "Core Commands",
            "commands": ["pdf", "validate", "init"],
        },
        {
            "name": "Content Commands",
            "commands": ["figures", "bibliography", "clean"],
        },
        {
            "name": "Workflow Commands",
            "commands": ["get-rxiv-preprint", "arxiv", "track-changes", "setup"],
        },
        {
            "name": "Configuration",
            "commands": ["cache", "config", "check-installation", "completion"],
        },
        {
            "name": "Information",
            "commands": ["version", "upgrade"],
        },
    ]
}

click.rich_click.OPTION_GROUPS = {
    "rxiv": [
        {
            "name": "Processing Options",
            "options": ["-v", "--verbose"],
        },
        {
            "name": "Setup Options",
            "options": ["--no-update-check"],
        },
        {
            "name": "Help & Version",
            "options": ["--help", "--version"],
        },
    ],
    "rxiv pdf": [
        {
            "name": "Build Options",
            "options": ["-o", "--output-dir", "-f", "--force-figures"],
        },
        {
            "name": "Processing Options",
            "options": [
                "-s",
                "--skip-validation",
                "-t",
                "--track-changes",
                "-v",
                "--verbose",
            ],
        },
        {
            "name": "Help",
            "options": ["--help"],
        },
    ],
    "rxiv validate": [
        {
            "name": "Validation Options",
            "options": ["-d", "--detailed", "--no-doi"],
        },
        {
            "name": "Help",
            "options": ["--help"],
        },
    ],
}

console = Console()


class UpdateCheckGroup(click.Group):
    """Custom Click group that handles update checking."""

    def invoke(self, ctx):
        """Invoke command and handle update checking."""
        try:
            # Start update check in background (non-blocking)
            check_for_updates_async()

            # Invoke the actual command
            result = super().invoke(ctx)

            # Show update notification after command completes
            # Only if command was successful and not disabled
            if not ctx.obj.get("no_update_check", False):
                show_update_notification()

            return result
        except Exception:
            # Always re-raise exceptions from commands
            raise


@click.group(cls=UpdateCheckGroup, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="rxiv")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--no-update-check", is_flag=True, help="Skip update check for this command")
@click.pass_context
def main(
    ctx: click.Context,
    verbose: bool,
    no_update_check: bool,
) -> None:
    """rxiv-maker converts Markdown manuscripts into publication-ready PDFs.

    \b
    Automated figure generation, professional LaTeX typesetting, and
    bibliography management using local execution only.

    \b
    QUICK START EXAMPLES
    ────────────────────

    \b
    Get help:
        $ rxiv --help

    \b
    Initialize a new manuscript:
        $ rxiv init MY_PAPER/

    \b
    Build PDF from manuscript:
        $ rxiv pdf                      # Build from MANUSCRIPT/
        $ rxiv pdf MY_PAPER/            # Build from custom directory
        $ rxiv pdf --force-figures      # Force regenerate figures

    \b
    Validate manuscript:
        $ rxiv validate                 # Validate current manuscript
        $ rxiv validate --no-doi        # Skip DOI validation

    \b
    Prepare arXiv submission:
        $ rxiv arxiv                    # Prepare arXiv package

    \b
    Install system dependencies:
        $ rxiv setup                    # Full setup
        $ rxiv setup --mode minimal     # Essential dependencies only

    \b
    Enable shell completion:
        $ rxiv completion zsh           # For zsh
        $ rxiv completion bash          # For bash

    \b
    NOTE: Rxiv-maker uses local-only execution for simplicity and reliability.
          For containerized execution, run rxiv-maker from within a Docker container.
    """
    # Initialize context
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["no_update_check"] = no_update_check

    # Set environment variables for local execution
    if verbose:
        os.environ["RXIV_VERBOSE"] = "1"
    if no_update_check:
        os.environ["RXIV_NO_UPDATE_CHECK"] = "1"


# Register command groups
main.add_command(commands.pdf, name="pdf")
main.add_command(commands.validate)
main.add_command(commands.clean)
main.add_command(commands.figures)
main.add_command(commands.get_rxiv_preprint, name="get-rxiv-preprint")
main.add_command(commands.arxiv)
main.add_command(commands.init)
main.add_command(commands.bibliography)
main.add_command(commands.track_changes)
main.add_command(commands.setup)
main.add_command(commands.version)
main.add_command(commands.upgrade)
main.add_command(commands.cache, name="cache")
main.add_command(commands.config, name="config")
main.add_command(check_installation, name="check-installation")
main.add_command(commands.completion_cmd, name="completion")
# Removed: containers command (deprecated with container engine support)

if __name__ == "__main__":
    main()
