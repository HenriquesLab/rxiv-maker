"""Main CLI entry point for rxiv-maker."""

import os
from pathlib import Path

import rich_click as click
from rich.console import Console

from .. import __version__
from ..utils.update_checker import check_for_updates_async, show_update_notification
from . import commands
from .commands.check_installation import check_installation
from .config import config_cmd

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
click.rich_click.STYLE_HELPTEXT = "dim"
click.rich_click.STYLE_USAGE = "yellow"
click.rich_click.STYLE_USAGE_COMMAND = "bold"
click.rich_click.STYLE_HELP_HEADER = "bold blue"
click.rich_click.STYLE_FOOTER_TEXT = "dim"
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
            "commands": ["arxiv", "track-changes", "setup", "install-deps"],
        },
        {
            "name": "Configuration",
            "commands": ["config", "check-installation"],
        },
        {
            "name": "Information",
            "commands": ["version"],
        },
    ]
}

click.rich_click.OPTION_GROUPS = {
    "rxiv": [
        {
            "name": "Processing Options",
            "options": ["-v", "--verbose", "--engine"],
        },
        {
            "name": "Setup Options",
            "options": ["--install-completion", "--no-update-check"],
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
    "rxiv init": [
        {
            "name": "Initialization Options",
            "options": ["-t", "--template", "-f", "--force"],
        },
        {
            "name": "Help",
            "options": ["--help"],
        },
    ],
}

console = Console()


class UpdateCheckGroup(click.Group):
    """Custom Click group that handles update checking and Docker cleanup."""

    def invoke(self, ctx):
        """Invoke command and handle update checking and Docker cleanup."""
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
        finally:
            # Clean up Docker sessions if Docker engine was used
            engine = ctx.obj.get("engine") if ctx.obj else None
            if engine == "docker":
                try:
                    from ..docker import cleanup_global_docker_manager

                    cleanup_global_docker_manager()
                except Exception:
                    # Ignore cleanup errors to avoid masking original exceptions
                    pass


@click.group(cls=UpdateCheckGroup, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="rxiv")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--engine",
    type=click.Choice(["local", "docker"]),
    default=lambda: os.environ.get("RXIV_ENGINE", "local").lower(),
    help="Engine to use for processing (local or docker). Can be set with RXIV_ENGINE environment variable.",
)
@click.option(
    "--install-completion",
    type=click.Choice(["bash", "zsh", "fish"]),
    help="Install shell completion for the specified shell",
)
@click.option("--no-update-check", is_flag=True, help="Skip update check for this command")
@click.pass_context
def main(
    ctx: click.Context,
    verbose: bool,
    engine: str,
    install_completion: str | None,
    no_update_check: bool,
) -> None:
    """**rxiv-maker** converts Markdown manuscripts into publication-ready PDFs.

    Automated figure generation, professional LaTeX typesetting, and bibliography
    management.

    ## Examples

    **Get help:**

        $ rxiv --help

    **Initialize a new manuscript:**

        $ rxiv init MY_PAPER/

    **Build PDF from manuscript:**

        $ rxiv pdf                      # Build from MANUSCRIPT/

        $ rxiv pdf MY_PAPER/            # Build from custom directory

        $ rxiv pdf --force-figures      # Force regenerate figures

    **Validate manuscript:**

        $ rxiv validate                 # Validate current manuscript

        $ rxiv validate --no-doi        # Skip DOI validation

    **Prepare arXiv submission:**

        $ rxiv arxiv                    # Prepare arXiv package

    **Install system dependencies:**

        $ rxiv install-deps             # Install LaTeX, Node.js, R, etc.

        $ rxiv install-deps --mode=minimal  # Install only essential dependencies
    """
    # Handle completion installation
    if install_completion:
        install_shell_completion(install_completion)
        return

    # Initialize context
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["engine"] = engine
    ctx.obj["no_update_check"] = no_update_check

    # Docker engine optimization: check Docker availability early
    if engine == "docker":
        from ..docker.manager import get_docker_manager

        try:
            if verbose:
                console.print("🐳 Creating Docker manager...", style="blue")
            # Use current working directory as workspace for consistency
            workspace_dir = Path.cwd().resolve()
            docker_manager = get_docker_manager(workspace_dir=workspace_dir)
            if verbose:
                console.print("🐳 Checking Docker availability...", style="blue")
            if not docker_manager.check_docker_available():
                console.print(
                    "❌ Docker is not available or not running. Please start Docker and try again.",
                    style="red",
                )
                console.print(
                    "💡 Alternatively, use --engine local for local execution",
                    style="yellow",
                )
                ctx.exit(1)

            if verbose:
                console.print("🐳 Docker is ready!", style="green")

        except Exception as e:
            if verbose:
                console.print(f"⚠️ Docker setup warning: {e}", style="yellow")

    # Set environment variables
    os.environ["RXIV_ENGINE"] = engine.upper()
    if verbose:
        os.environ["RXIV_VERBOSE"] = "1"
    if no_update_check:
        os.environ["RXIV_NO_UPDATE_CHECK"] = "1"


def install_shell_completion(shell: str) -> None:
    """Install shell completion for the specified shell."""
    console.print(f"Installing {shell} completion...", style="blue")

    try:
        if shell == "bash":
            completion_script = "_RXIV_COMPLETE=bash_source rxiv"
            install_path = Path.home() / ".bashrc"

        elif shell == "zsh":
            completion_script = "_RXIV_COMPLETE=zsh_source rxiv"
            install_path = Path.home() / ".zshrc"

        elif shell == "fish":
            completion_script = "_RXIV_COMPLETE=fish_source rxiv"
            install_path = Path.home() / ".config/fish/config.fish"

        # Add completion to shell config
        completion_line = f'eval "$({completion_script})"'

        # Check if already installed
        if install_path.exists():
            content = install_path.read_text()
            if completion_line in content:
                console.print(f"✅ {shell} completion already installed", style="green")
                return

        # Add completion
        with open(install_path, "a", encoding="utf-8") as f:
            f.write(f"\n# Rxiv-Maker completion\n{completion_line}\n")

        console.print(f"✅ {shell} completion installed to {install_path}", style="green")
        console.print(f"💡 Restart your shell or run: source {install_path}", style="yellow")

    except Exception as e:
        console.print(f"❌ Error installing completion: {e}", style="red")


# Register command groups
main.add_command(commands.pdf, name="pdf")
main.add_command(commands.validate)
main.add_command(commands.clean)
main.add_command(commands.figures)
main.add_command(commands.arxiv)
main.add_command(commands.init)
main.add_command(commands.bibliography)
main.add_command(commands.track_changes)
main.add_command(commands.setup)
main.add_command(commands.install_deps, name="install-deps")
main.add_command(commands.version)
main.add_command(config_cmd, name="config")
main.add_command(check_installation, name="check-installation")

if __name__ == "__main__":
    main()
