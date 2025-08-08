"""Shell completion installation command."""

from pathlib import Path

import rich_click as click
from rich.console import Console

console = Console()


@click.command("completion")
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def completion_cmd(shell: str) -> None:
    """Install shell completion for the specified shell.

    This command sets up auto-completion for the rxiv command in your shell.
    After installation, you'll be able to use Tab to complete commands and options.

    Examples:
        rxiv completion zsh     # Install for zsh

        rxiv completion bash    # Install for bash

        rxiv completion fish    # Install for fish
    """
    install_shell_completion(shell)


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
