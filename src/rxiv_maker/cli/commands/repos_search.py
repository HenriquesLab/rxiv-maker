"""Repos-search command for rxiv-maker CLI."""

import logging
import sys

import click
from rich.console import Console
from rich.table import Table

from ...core.repo_config import get_repo_config
from ...core.repository import RepositoryManager
from ...utils.github import (
    GitHubError,
    check_gh_auth,
    check_gh_cli_installed,
    clone_github_repo,
    list_github_repos,
)
from ..interactive import prompt_confirm, prompt_confirm_with_path_change, prompt_multi_select

console = Console()
logger = logging.getLogger(__name__)


@click.command(name="repos-search", context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("github_org", required=False)
@click.option("--pattern", default="manuscript-", help="Repository name pattern to match")
@click.option("--no-interactive", is_flag=True, help="Non-interactive mode (list only)")
@click.pass_context
def repos_search(
    ctx: click.Context,
    github_org: str,
    pattern: str,
    no_interactive: bool,
) -> None:
    """Search for manuscript repositories on GitHub.

    Searches a GitHub organization for manuscript-* repositories and optionally clones them.

    Examples:
        $ rxiv repos-search my-lab

        $ rxiv repos-search my-lab --pattern manuscript-

        $ rxiv repos-search --no-interactive my-lab
    """
    config = get_repo_config()
    repo_manager = RepositoryManager(config)

    # Check prerequisites
    if not check_gh_cli_installed():
        console.print("[red]Error: GitHub CLI (gh) is not installed[/red]")
        console.print("Install it with: brew install gh")
        sys.exit(1)

    if not check_gh_auth():
        console.print("[red]Error: Not authenticated with GitHub CLI[/red]")
        console.print("Run: gh auth login")
        sys.exit(1)

    # Get organization
    if not github_org:
        github_org = config.default_github_org

    if not github_org:
        console.print("[red]Error: GitHub organization not specified[/red]")
        console.print("Usage: rxiv repos-search ORGANIZATION")
        console.print("Or set default: rxiv repo-init")
        sys.exit(1)

    # Search for repositories
    try:
        console.print(f"\n[cyan]Searching for repositories in {github_org}...[/cyan]\n")

        github_repos = list_github_repos(github_org, pattern)

        if not github_repos:
            console.print(f"[yellow]No repositories found matching pattern '{pattern}' in {github_org}[/yellow]")
            return

        # Check which ones are already cloned
        local_repos = repo_manager.discover_repositories(config.parent_dir)
        local_repo_names = {f"manuscript-{r.name}" for r in local_repos}

        repos_to_display = []
        unclaimed_repos = []

        for github_repo in github_repos:
            repo_name = github_repo["name"]
            is_cloned = repo_name in local_repo_names

            repos_to_display.append(
                {
                    "name": repo_name,
                    "url": github_repo["url"],
                    "is_cloned": is_cloned,
                }
            )

            if not is_cloned:
                unclaimed_repos.append(github_repo)

        # Display table
        table = Table(title=f"Manuscript Repositories in {github_org}")

        table.add_column("#", style="dim", width=4)
        table.add_column("Repository Name", style="bold cyan")
        table.add_column("Status", justify="center")
        table.add_column("URL", style="dim")

        for idx, repo_info in enumerate(repos_to_display, 1):
            status = "[green]cloned[/green]" if repo_info["is_cloned"] else "[yellow]not cloned[/yellow]"

            table.add_row(
                str(idx),
                repo_info["name"],
                status,
                repo_info["url"],
            )

        console.print(table)
        console.print()

        # Summary
        console.print(f"Found {len(github_repos)} repositories")
        console.print(f"Already cloned: {len(github_repos) - len(unclaimed_repos)}")
        console.print(f"Available to clone: {len(unclaimed_repos)}")
        console.print()

        # Interactive cloning
        if unclaimed_repos and not no_interactive:
            # Get confirmation with optional path change
            proceed, final_path = prompt_confirm_with_path_change(
                current_path=config.parent_dir,
                action_description="Clone repositories",
            )

            if proceed:
                # Update config if path changed
                if final_path != config.parent_dir:
                    config.parent_dir = str(final_path)
                    console.print(f"[dim]Updated parent directory to: {final_path}[/dim]\n")

                # Ensure parent directory exists (safety check)
                final_path.mkdir(parents=True, exist_ok=True)

                # Interactive selection using checkboxes
                if len(unclaimed_repos) == 1:
                    # Just one repo, ask directly
                    repo = unclaimed_repos[0]
                    if prompt_confirm(f"Clone {repo['name']}?", default=True):
                        selected_repos = [repo]
                    else:
                        selected_repos = []
                else:
                    # Multiple repos, use checkbox dialog
                    choices = [(repo["name"], repo["name"]) for repo in unclaimed_repos]

                    try:
                        result = prompt_multi_select(
                            title="Select repositories to clone",
                            items=choices,
                        )

                        if result:
                            selected_names = set(result)
                            selected_repos = [r for r in unclaimed_repos if r["name"] in selected_names]
                        else:
                            selected_repos = []

                    except KeyboardInterrupt:
                        # Allow user to cancel with Ctrl+C
                        raise
                    except Exception as e:
                        # Fallback if dialog doesn't work (terminal compatibility issues, etc.)
                        logger.debug(f"Interactive dialog failed: {e}")
                        console.print("\n[yellow]Interactive selection unavailable, using simple prompts[/yellow]\n")
                        selected_repos = []
                        for repo in unclaimed_repos:
                            if prompt_confirm(f"Clone {repo['name']}?", default=False):
                                selected_repos.append(repo)

                # Clone selected repositories
                if selected_repos:
                    console.print(f"\n[cyan]Cloning {len(selected_repos)} repositories...[/cyan]\n")

                    for repo in selected_repos:
                        repo_name = repo["name"]
                        target_path = final_path / repo_name

                        try:
                            console.print(f"Cloning {repo_name}...")
                            clone_github_repo(github_org, repo_name, target_path)
                            console.print(f"[green]✓[/green] Cloned to {target_path}")

                        except GitHubError as e:
                            console.print(f"[red]✗[/red] Failed to clone {repo_name}: {e}")

                    console.print("\n[green]✓ Cloning complete![/green]")

                else:
                    console.print("\nNo repositories selected")

    except GitHubError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)
