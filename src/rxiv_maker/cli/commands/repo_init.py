"""Repo-init command for rxiv-maker CLI."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ...core.repo_config import get_repo_config
from ...core.repository import RepositoryManager
from ...utils.github import GitHubError, get_github_orgs
from ..interactive import prompt_confirm, prompt_text

console = Console()


@click.command(name="repo-init", context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--parent-dir", type=click.Path(path_type=Path), help="Parent directory for manuscript repositories")
@click.option("--github-org", help="Default GitHub organization")
@click.option("--no-interactive", is_flag=True, help="Non-interactive mode")
@click.pass_context
def repo_init(
    ctx: click.Context,
    parent_dir: Path,
    github_org: str,
    no_interactive: bool,
) -> None:
    """Initialize repository management configuration.

    Sets up the parent directory for manuscript repositories and default GitHub organization.

    Examples:
        $ rxiv repo-init

        $ rxiv repo-init --parent-dir ~/manuscripts --github-org my-lab
    """
    config = get_repo_config()

    # Check if already configured
    existing_config = config.load()
    is_reconfigure = config.config_path.exists()

    if is_reconfigure and not no_interactive:
        console.print("\n[yellow]Repository management is already configured[/yellow]\n")
        console.print(f"Parent directory: {config.parent_dir}")
        if config.default_github_org:
            console.print(f"Default GitHub org: {config.default_github_org}")

        if not prompt_confirm("\nReconfigure?", default=False):
            console.print("\nCancelled")
            return

    console.print("\n[bold cyan]Repository Management Setup[/bold cyan]\n")

    # Create repository manager
    repo_manager = RepositoryManager(config)

    # Interactive mode
    if not no_interactive:
        # Scan for existing repositories
        console.print("[cyan]Scanning for existing manuscript repositories...[/cyan]\n")

        scan_locations = [Path.cwd(), Path.cwd().parent]

        home = Path.home()
        for common_dir in ["Code", "GitHub", "Projects", "Documents", "manuscripts", "work"]:
            potential_path = home / common_dir
            if potential_path.exists():
                scan_locations.append(potential_path)
        found_locations = {}

        for location in scan_locations:
            repos_dict = repo_manager.scan_for_manuscript_repositories(location, max_depth=2)
            if repos_dict:
                found_locations.update(repos_dict)

        # Show found repositories
        if found_locations:
            console.print("[green]Found manuscript repositories:[/green]\n")

            for location, repos in found_locations.items():
                console.print(f"  {location}:")
                for repo in repos:
                    console.print(f"    - manuscript-{repo.name}")
                console.print()

        # Get parent directory
        if not parent_dir:
            if found_locations:
                suggested_parent = list(found_locations.keys())[0]
            elif existing_config.get("repo_parent_dir"):
                suggested_parent = existing_config["repo_parent_dir"]
            else:
                suggested_parent = str(home / "manuscripts")

            parent_dir_input = prompt_text(
                "Parent directory for manuscript repositories: ",
                default=suggested_parent,
            )

            parent_dir = Path(parent_dir_input).expanduser()

        # Create parent directory if it doesn't exist
        if not parent_dir.exists():
            console.print(f"\n[yellow]Directory does not exist: {parent_dir}[/yellow]")
            if prompt_confirm("Create it?", default=True):
                parent_dir.mkdir(parents=True, exist_ok=True)
                console.print("[green]✓[/green] Created directory")
            else:
                console.print("[yellow]Warning: Parent directory does not exist[/yellow]")

        # Get GitHub organization
        if not github_org:
            try:
                orgs = get_github_orgs()
                if orgs:
                    console.print(f"\nAvailable GitHub organizations: {', '.join(orgs)}")
                    default_org = existing_config.get("repo_default_github_org") or orgs[0]
                else:
                    default_org = existing_config.get("repo_default_github_org")
            except GitHubError:
                console.print("\n[yellow]Warning: Could not fetch GitHub organizations[/yellow]")
                console.print("GitHub CLI may not be installed or authenticated")
                default_org = existing_config.get("repo_default_github_org")

            github_org = prompt_text(
                "Default GitHub organization (optional): ",
                default=default_org or "",
            )

    # Non-interactive mode
    else:
        if not parent_dir:
            console.print("[red]Error: --parent-dir is required in non-interactive mode[/red]")
            sys.exit(1)

        # Create parent directory if requested
        if not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)

    # Save configuration
    config.parent_dir = str(parent_dir)
    if github_org:
        config.default_github_org = github_org

    console.print("\n[green]✓ Repository management configured[/green]\n")

    # Show summary
    table = Table(title="Configuration", show_header=False, box=None)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Parent Directory", str(config.parent_dir))
    table.add_row("Expanded Path", str(config.parent_dir.expanduser().resolve()))

    if config.default_github_org:
        table.add_row("Default GitHub Org", config.default_github_org)

    table.add_row("Config File", str(config.config_path))

    console.print(table)
    console.print()

    # Discover and show repositories
    repos = repo_manager.discover_repositories(config.parent_dir)

    if repos:
        console.print(f"[green]Found {len(repos)} manuscript repositories[/green]")
        for repo in repos[:5]:  # Show first 5
            console.print(f"  - manuscript-{repo.name}")
        if len(repos) > 5:
            console.print(f"  ... and {len(repos) - 5} more")
    else:
        console.print("[dim]No manuscript repositories found[/dim]")
        console.print("\nCreate your first repository with: rxiv create-repo NAME")

    console.print()
