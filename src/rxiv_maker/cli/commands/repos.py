"""Repos command for rxiv-maker CLI."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ...core.repo_config import get_repo_config
from ...core.repository import RepositoryManager

console = Console()


@click.command(name="repos", context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "list", "paths"]),
    default="table",
    help="Output format",
)
@click.option("--parent-dir", type=click.Path(path_type=Path), help="Parent directory to search (overrides config)")
@click.pass_context
def repos(
    ctx: click.Context,
    output_format: str,
    parent_dir: Path,
) -> None:
    """List all manuscript repositories.

    Shows all manuscript-* repositories in the configured parent directory.

    Examples:
        $ rxiv repos

        $ rxiv repos --format list

        $ rxiv repos --parent-dir ~/projects/manuscripts
    """
    config = get_repo_config()
    repo_manager = RepositoryManager(config)

    # Use specified parent_dir or get from config
    if parent_dir:
        search_dir = parent_dir
    else:
        search_dir = config.parent_dir

    if not search_dir.exists():
        console.print(f"[yellow]Parent directory does not exist: {search_dir}[/yellow]")
        console.print("\nRun 'rxiv repo-init' to configure repository management")
        return

    # Discover repositories
    repos = repo_manager.discover_repositories(search_dir)

    if not repos:
        console.print(f"[yellow]No manuscript repositories found in: {search_dir}[/yellow]")
        console.print("\nCreate a repository with: rxiv create-repo NAME")
        return

    # Output based on format
    if output_format == "paths":
        for repo in repos:
            console.print(str(repo.path))

    elif output_format == "list":
        for repo in repos:
            status_info = []

            # Git status
            if repo.is_git_repository():
                git_status = repo.get_git_status()
                if git_status:
                    if git_status["is_dirty"]:
                        status_info.append("[yellow]modified[/yellow]")
                    if git_status["untracked_files"] > 0:
                        status_info.append(f"[yellow]{git_status['untracked_files']} untracked[/yellow]")
                    if git_status["ahead"] > 0:
                        status_info.append(f"[cyan]↑{git_status['ahead']}[/cyan]")
                    if git_status["behind"] > 0:
                        status_info.append(f"[cyan]↓{git_status['behind']}[/cyan]")

                    status_str = " ".join(status_info) if status_info else "[green]clean[/green]"
                else:
                    status_str = "[dim]git[/dim]"
            else:
                status_str = "[dim]no git[/dim]"

            # Manuscript directory
            manuscript_status = "[green]✓[/green]" if repo.has_manuscript_dir() else "[red]✗[/red]"

            console.print(f"{repo.name:30s} {manuscript_status} {status_str}")

    else:  # table format (default)
        table = Table(title=f"Manuscript Repositories in {search_dir}", show_lines=False)

        table.add_column("Name", style="bold cyan", no_wrap=True)
        table.add_column("Path", style="dim")
        table.add_column("Git Status", justify="center")
        table.add_column("MANUSCRIPT", justify="center")
        table.add_column("Last Modified")

        for repo in repos:
            # Git status
            if repo.is_git_repository():
                git_status = repo.get_git_status()
                if git_status:
                    status_parts = []
                    if git_status["is_dirty"]:
                        status_parts.append("modified")
                    if git_status["untracked_files"] > 0:
                        status_parts.append(f"{git_status['untracked_files']} untracked")
                    if git_status["ahead"] > 0:
                        status_parts.append(f"↑{git_status['ahead']}")
                    if git_status["behind"] > 0:
                        status_parts.append(f"↓{git_status['behind']}")

                    if status_parts:
                        git_status_str = ", ".join(status_parts)
                        git_status_color = "yellow"
                    else:
                        git_status_str = "clean"
                        git_status_color = "green"

                    # Add branch info
                    branch = git_status.get("branch", "unknown")
                    git_status_str = f"[dim]{branch}[/dim]\n[{git_status_color}]{git_status_str}[/{git_status_color}]"
                else:
                    git_status_str = "[dim]git repo[/dim]"
            else:
                git_status_str = "[dim]no git[/dim]"

            # Manuscript directory status
            manuscript_status = "[green]✓[/green]" if repo.has_manuscript_dir() else "[red]✗[/red]"

            # Last modified
            last_modified = repo.get_last_modified()
            if last_modified:
                last_modified_str = last_modified.strftime("%Y-%m-%d %H:%M")
            else:
                last_modified_str = "[dim]unknown[/dim]"

            # Path (relative to parent if possible)
            try:
                rel_path = repo.path.relative_to(search_dir)
                path_str = f"./{rel_path}"
            except ValueError:
                path_str = str(repo.path)

            table.add_row(
                repo.name,
                path_str,
                git_status_str,
                manuscript_status,
                last_modified_str,
            )

        console.print()
        console.print(table)
        console.print()
        console.print(f"[dim]Found {len(repos)} manuscript repositories[/dim]")

        # Show config info
        if not parent_dir:
            console.print(f"[dim]Parent directory: {config.parent_dir}[/dim]")
            if config.default_github_org:
                console.print(f"[dim]Default GitHub org: {config.default_github_org}[/dim]")
