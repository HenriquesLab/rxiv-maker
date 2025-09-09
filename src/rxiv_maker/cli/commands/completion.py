"""Shell completion installation command."""

import rich_click as click

from ..framework import CompletionCommand


@click.command("completion")
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
@click.pass_context
def completion_cmd(ctx: click.Context, shell: str) -> None:
    """Install shell completion for the specified shell.

    This command sets up auto-completion for the rxiv command in your shell.
    After installation, you'll be able to use Tab to complete commands and options.

    Examples:
        rxiv completion zsh     # Install for zsh

        rxiv completion bash    # Install for bash

        rxiv completion fish    # Install for fish
    """
    command = CompletionCommand()
    return command.run(ctx, manuscript_path=None, shell=shell)
