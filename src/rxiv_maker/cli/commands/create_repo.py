"""Create repository command for rxiv-maker CLI."""

import subprocess
import sys

import click
from rich.console import Console

from ...core.repo_config import get_repo_config
from ...core.repository import RepositoryManager
from ...utils.github import (
    GitHubError,
    check_gh_auth,
    check_gh_cli_installed,
    check_github_repo_exists,
    create_github_repo,
    get_github_orgs,
    push_to_remote,
    setup_git_remote,
    validate_github_name,
)
from ..interactive import prompt_confirm, prompt_text

console = Console()


@click.command(name="create-repo", context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("name", required=False)
@click.option("--github-org", help="GitHub organization for repository")
@click.option(
    "--visibility", type=click.Choice(["public", "private"]), default="public", help="Repository visibility on GitHub"
)
@click.option("--no-github", is_flag=True, help="Skip GitHub integration")
@click.option("--no-interactive", is_flag=True, help="Non-interactive mode (requires --name)")
@click.pass_context
def create_repo(
    ctx: click.Context,
    name: str,
    github_org: str,
    visibility: str,
    no_github: bool,
    no_interactive: bool,
) -> None:
    """Create a new manuscript repository.

    Creates a manuscript-{NAME} directory with MANUSCRIPT folder structure.

    Examples:
        $ rxiv create-repo my-paper

        $ rxiv create-repo my-paper --github-org my-lab --visibility private

        $ rxiv create-repo --no-github my-paper
    """
    config = get_repo_config()
    repo_manager = RepositoryManager(config)

    # Interactive mode
    if not no_interactive:
        # Get repository name
        if not name:
            console.print("\n[bold cyan]Create Manuscript Repository[/bold cyan]\n")
            name = prompt_text("Repository name (without 'manuscript-' prefix): ", default="")

            if not name:
                console.print("[red]Error: Repository name is required[/red]")
                sys.exit(1)

        # Check if repository already exists
        if repo_manager.get_repository(name):
            console.print(f"[red]Error: Repository 'manuscript-{name}' already exists[/red]")
            sys.exit(1)

        # Ask about GitHub integration
        if not no_github:
            github_enabled = prompt_confirm("\nEnable GitHub integration?", default=True)

            if github_enabled:
                # Check prerequisites
                if not check_gh_cli_installed():
                    console.print(
                        "[yellow]Warning: GitHub CLI (gh) is not installed. Skipping GitHub integration.[/yellow]"
                    )
                    console.print("Install it with: brew install gh")
                    github_enabled = False
                elif not check_gh_auth():
                    console.print("[yellow]Warning: Not authenticated with GitHub CLI.[/yellow]")
                    console.print("Run: gh auth login")
                    github_enabled = False

                if github_enabled:
                    # Get organization
                    if not github_org:
                        try:
                            orgs = get_github_orgs()
                            if orgs:
                                console.print(f"\nAvailable organizations: {', '.join(orgs)}")
                                default_org = config.default_github_org or orgs[0]
                            else:
                                default_org = config.default_github_org
                        except GitHubError:
                            default_org = config.default_github_org

                        github_org = prompt_text(
                            "GitHub organization: ",
                            default=default_org or "",
                        )

                        if not github_org:
                            console.print("[yellow]No organization provided. Skipping GitHub integration.[/yellow]")
                            github_enabled = False

                    # Get visibility
                    if github_enabled:
                        visibility = "private" if prompt_confirm("Private repository?", default=False) else "public"

                        # Check if repo already exists on GitHub
                        try:
                            if check_github_repo_exists(github_org, f"manuscript-{name}"):
                                console.print(
                                    f"[yellow]Warning: Repository {github_org}/manuscript-{name} already exists on GitHub[/yellow]"
                                )
                                if not prompt_confirm("Continue with local repository only?", default=True):
                                    sys.exit(0)
                                github_enabled = False
                        except GitHubError as e:
                            console.print(f"[yellow]Warning: Could not check GitHub repository: {e}[/yellow]")
                            if not prompt_confirm("Continue anyway?", default=True):
                                sys.exit(0)
            else:
                github_enabled = False
        else:
            github_enabled = False

    else:
        # Non-interactive mode
        if not name:
            console.print("[red]Error: Repository name is required in non-interactive mode[/red]")
            sys.exit(1)

        # Validate repository name
        try:
            validate_github_name(name, "repository")
        except ValueError as e:
            console.print(f"[red]Error: Invalid repository name: {e}[/red]")
            sys.exit(1)

        # Check if repository already exists
        if repo_manager.get_repository(name):
            console.print(f"[red]Error: Repository 'manuscript-{name}' already exists[/red]")
            sys.exit(1)

        github_enabled = not no_github and github_org is not None

        if github_enabled:
            if not check_gh_cli_installed() or not check_gh_auth():
                console.print("[red]Error: GitHub CLI not available or not authenticated[/red]")
                sys.exit(1)

    # Create local repository
    try:
        console.print(f"\n[cyan]Creating repository: manuscript-{name}[/cyan]")

        repo = repo_manager.create_repository(
            name=name,
            init_git=True,
            create_manuscript_dir=True,
        )

        console.print(f"[green]✓[/green] Created repository at: {repo.path}")

        # Initialize manuscript structure using rxiv init
        console.print("[cyan]Initializing MANUSCRIPT directory...[/cyan]")

        try:
            result = subprocess.run(
                ["rxiv", "init", str(repo.manuscript_dir), "--no-interactive"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                console.print("[green]✓[/green] Initialized MANUSCRIPT structure")
            else:
                console.print("[yellow]Warning: Failed to initialize MANUSCRIPT directory[/yellow]")
                console.print(result.stderr or result.stdout)

            # Add files to git
            if repo.is_git_repository():
                # Add only safe, expected files to avoid accidentally committing sensitive data
                files_to_add = []
                safe_paths = ["MANUSCRIPT/", ".gitignore", "README.md", "LICENSE"]

                for safe_path in safe_paths:
                    full_path = repo.path / safe_path
                    if full_path.exists():
                        files_to_add.append(safe_path)

                if files_to_add:
                    repo.git_repo.index.add(files_to_add)
                    repo.git_repo.index.commit("Initial commit with MANUSCRIPT structure")
                    console.print(f"[green]✓[/green] Created initial commit with: {', '.join(files_to_add)}")

        except Exception as e:
            console.print(f"[yellow]Warning: Failed to initialize MANUSCRIPT: {e}[/yellow]")

        # GitHub integration
        if github_enabled and github_org:
            try:
                console.print(f"\n[cyan]Creating GitHub repository: {github_org}/manuscript-{name}[/cyan]")

                github_url = create_github_repo(github_org, f"manuscript-{name}", visibility)

                console.print(f"[green]✓[/green] Created GitHub repository: {github_url}")

                # Setup remote and push
                setup_git_remote(repo.path, github_url)
                console.print("[green]✓[/green] Added remote 'origin'")

                # Determine default branch name
                try:
                    branch_result = subprocess.run(
                        ["git", "branch", "--show-current"],
                        cwd=repo.path,
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    branch = branch_result.stdout.strip() or "main"
                except Exception:
                    branch = "main"

                push_to_remote(repo.path, branch)
                console.print(f"[green]✓[/green] Pushed to {github_url}")

            except GitHubError as e:
                console.print(f"[yellow]Warning: GitHub integration failed: {e}[/yellow]")
                console.print("[yellow]Repository created locally only[/yellow]")

        # Success message
        console.print("\n[bold green]✓ Repository created successfully![/bold green]")
        console.print("\nNext steps:")
        console.print(f"  1. cd {repo.path}")
        console.print("  2. Edit MANUSCRIPT/01_MAIN.md with your content")
        console.print("  3. rxiv pdf MANUSCRIPT/")

    except Exception as e:
        console.print(f"[red]Error creating repository: {e}[/red]")
        sys.exit(1)
