"""CLI commands for configuration management and validation."""

import contextlib
import io
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from ...core.managers.config_manager import get_config_manager
from ...core.repo_config import get_repo_config
from ...core.repository import RepositoryManager
from ..framework import (
    ConfigExportCommand,
    ConfigGetCommand,
    ConfigInitCommand,
    ConfigListCommand,
    ConfigMigrateCommand,
    ConfigShowCommand,
    ConfigValidateCommand,
)
from ..interactive import (
    prompt_editor,
    prompt_github_org,
    prompt_path,
    prompt_text,
)

console = Console()


@contextlib.contextmanager
def suppress_stderr():
    """Context manager to temporarily suppress stderr output."""
    old_stderr = sys.stderr
    sys.stderr = io.StringIO()
    try:
        yield
    finally:
        sys.stderr = old_stderr


def config_exists_quietly() -> bool:
    """Check if manuscript config exists without printing errors."""
    config_manager = get_config_manager()
    with suppress_stderr():
        config_file = config_manager._find_existing_config()
        return config_file is not None and config_file.exists()


@click.group(name="config", invoke_without_command=True)
@click.option("--non-interactive", is_flag=True, help="Non-interactive mode (show current configs)")
@click.pass_context
def config_group(ctx: click.Context, non_interactive: bool):
    """Configuration management (interactive by default).

    Run 'rxiv config' for interactive menu.
    Use '--non-interactive' to show current configuration.
    Or use specific subcommands for direct access.
    """
    # If a subcommand is invoked, let it handle the request
    if ctx.invoked_subcommand is not None:
        return

    # No subcommand = interactive mode (or show config if --non-interactive)
    if non_interactive:
        show_all_configs_summary()
    else:
        run_interactive_config_menu()


@config_group.command()
@click.option(
    "--template",
    type=click.Choice(["default", "minimal", "journal", "preprint"]),
    default="default",
    help="Configuration template to use",
)
@click.option("--force", is_flag=True, help="Overwrite existing configuration file")
@click.option("--output", type=click.Path(path_type=Path), help="Output path for configuration file")
@click.pass_context
def init(ctx: click.Context, template: str, force: bool, output: Optional[Path] = None):
    """Initialize configuration file from template."""
    command = ConfigInitCommand()
    return command.run(
        ctx, manuscript_path=None, template=template, force=force, output=str(output) if output else None
    )


@config_group.command()
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file to validate",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format for validation results",
)
@click.option("--strict", is_flag=True, help="Use strict validation mode")
@click.pass_context
def validate(
    ctx: click.Context, config_path: Optional[Path] = None, output_format: str = "table", strict: bool = False
):
    """Validate configuration file."""
    command = ConfigValidateCommand()
    return command.run(
        ctx,
        manuscript_path=None,
        config_path=str(config_path) if config_path else None,
        output_format=output_format,
        strict=strict,
    )


@config_group.command()
@click.argument("key")
@click.argument("value", required=False)
@click.option("--config", "config_path", type=click.Path(path_type=Path), help="Path to configuration file")
@click.option(
    "--type",
    "value_type",
    type=click.Choice(["string", "int", "float", "bool", "json"]),
    default="string",
    help="Value type for setting values",
)
@click.pass_context
def get(
    ctx: click.Context,
    key: str,
    value: Optional[str] = None,
    config_path: Optional[Path] = None,
    value_type: str = "string",
):
    """Get or set configuration values."""
    command = ConfigGetCommand()
    return command.run(
        ctx,
        manuscript_path=None,
        key=key,
        value=value,
        config_path=str(config_path) if config_path else None,
        value_type=value_type,
    )


@config_group.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format for configuration display",
)
@click.option(
    "--config", "config_path", type=click.Path(exists=True, path_type=Path), help="Path to specific configuration file"
)
@click.option("--include-defaults", is_flag=True, help="Include default values in output")
@click.pass_context
def show(
    ctx: click.Context, output_format: str = "table", config_path: Optional[Path] = None, include_defaults: bool = False
):
    """Show current configuration."""
    command = ConfigShowCommand()
    return command.run(
        ctx,
        manuscript_path=None,
        output_format=output_format,
        config_path=str(config_path) if config_path else None,
        include_defaults=include_defaults,
    )


@config_group.command()
@click.option("--output", type=click.Path(path_type=Path), required=True, help="Output path for exported configuration")
@click.option("--format", "export_format", type=click.Choice(["yaml", "json"]), default="yaml", help="Export format")
@click.option("--include-defaults", is_flag=True, help="Include default values in export")
@click.option(
    "--config", "config_path", type=click.Path(exists=True, path_type=Path), help="Path to configuration file to export"
)
@click.pass_context
def export(
    ctx: click.Context, output: Path, export_format: str, include_defaults: bool, config_path: Optional[Path] = None
):
    """Export configuration to file."""
    command = ConfigExportCommand()
    return command.run(
        ctx,
        manuscript_path=None,
        output=str(output),
        export_format=export_format,
        include_defaults=include_defaults,
        config_path=str(config_path) if config_path else None,
    )


@config_group.command()
@click.option("--from-version", required=True, help="Current configuration version")
@click.option("--to-version", required=True, help="Target configuration version")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file to migrate",
)
@click.option("--backup/--no-backup", default=True, help="Create backup before migration")
@click.pass_context
def migrate(
    ctx: click.Context, from_version: str, to_version: str, config_path: Optional[Path] = None, backup: bool = True
):
    """Migrate configuration from one version to another."""
    command = ConfigMigrateCommand()
    return command.run(
        ctx,
        manuscript_path=None,
        from_version=from_version,
        to_version=to_version,
        config_path=str(config_path) if config_path else None,
        backup=backup,
    )


@config_group.command()
@click.pass_context
def list_files(ctx: click.Context):
    """List all configuration files and their status."""
    command = ConfigListCommand()
    return command.run(ctx, manuscript_path=None)


# ============================================================================
# Global Repository Configuration Commands
# ============================================================================


@config_group.command(name="show-repo")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "yaml", "json"]),
    default="table",
    help="Output format",
)
@click.pass_context
def show_repo(ctx: click.Context, output_format: str = "table"):
    """Show global repository configuration (stored in ~/.rxiv-maker/config).

    This shows repository management settings like parent directory and
    default GitHub organization, separate from manuscript-level configuration.

    Examples:
        $ rxiv config show-repo

        $ rxiv config show-repo --format yaml
    """
    import json

    import yaml

    repo_config = get_repo_config()
    config_data = repo_config.show()

    if output_format == "yaml":
        console.print(yaml.dump(config_data, default_flow_style=False, sort_keys=False))
    elif output_format == "json":
        console.print(json.dumps(config_data, indent=2))
    else:
        # Table format
        table = Table(title="Global Repository Configuration", show_header=False, box=None)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")

        # Show configuration
        table.add_row("Parent Directory", str(config_data.get("repo_parent_dir", "Not set")))
        table.add_row("Expanded Path", str(config_data.get("repo_parent_dir_expanded", "N/A")))

        if config_data.get("repo_default_github_org"):
            table.add_row("Default GitHub Org", config_data["repo_default_github_org"])
        else:
            table.add_row("Default GitHub Org", "[dim]Not set[/dim]")

        if config_data.get("repo_default_editor"):
            table.add_row("Default Editor", config_data["repo_default_editor"])

        table.add_row("Auto Sync", str(config_data.get("repo_auto_sync", False)))
        table.add_row("Config File", str(repo_config.config_path))

        console.print()
        console.print(table)
        console.print()
        console.print("[dim]This is global repository configuration (not manuscript-specific)[/dim]")
        console.print("[dim]For manuscript configuration, use: rxiv config show[/dim]")


@config_group.command(name="set-repo-parent-dir")
@click.argument("parent_dir", type=click.Path(path_type=Path))
@click.option("--create", is_flag=True, help="Create directory if it doesn't exist")
@click.pass_context
def set_repo_parent_dir(ctx: click.Context, parent_dir: Path, create: bool):
    """Set parent directory for manuscript repositories.

    This is global repository configuration (stored in ~/.rxiv-maker/config).

    Examples:
        $ rxiv config set-repo-parent-dir ~/manuscripts

        $ rxiv config set-repo-parent-dir ~/work/papers --create
    """
    repo_config = get_repo_config()

    # Expand and resolve path
    parent_dir = parent_dir.expanduser().resolve()

    # Check if directory exists
    if not parent_dir.exists():
        if create:
            parent_dir.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]✓[/green] Created directory: {parent_dir}")
        else:
            console.print(f"[yellow]Warning: Directory does not exist: {parent_dir}[/yellow]")
            console.print("Use --create to create it")

    # Set configuration
    repo_config.parent_dir = str(parent_dir)

    console.print(f"\n[green]✓[/green] Set repository parent directory to: {parent_dir}")
    console.print(f"\n[dim]Config saved to: {repo_config.config_path}[/dim]")


@config_group.command(name="set-repo-org")
@click.argument("github_org")
@click.pass_context
def set_repo_org(ctx: click.Context, github_org: str):
    """Set default GitHub organization for manuscript repositories.

    This is global repository configuration (stored in ~/.rxiv-maker/config).

    Examples:
        $ rxiv config set-repo-org my-lab

        $ rxiv config set-repo-org my-username
    """
    repo_config = get_repo_config()
    repo_config.default_github_org = github_org

    console.print(f"\n[green]✓[/green] Set default GitHub organization to: {github_org}")
    console.print(f"\n[dim]Config saved to: {repo_config.config_path}[/dim]")


@config_group.command(name="set-repo-editor")
@click.argument("editor")
@click.pass_context
def set_repo_editor(ctx: click.Context, editor: str):
    """Set default editor for manuscript repositories.

    This is global repository configuration (stored in ~/.rxiv-maker/config).

    Examples:
        $ rxiv config set-repo-editor code

        $ rxiv config set-repo-editor vim
    """
    repo_config = get_repo_config()
    repo_config.default_editor = editor

    console.print(f"\n[green]✓[/green] Set default editor to: {editor}")
    console.print(f"\n[dim]Config saved to: {repo_config.config_path}[/dim]")


# ============================================================================
# Interactive Menu Functions
# ============================================================================


def show_all_configs_summary():
    """Show both manuscript and repo configs in non-interactive mode."""
    console.print("\n[bold cyan]Manuscript Configuration[/bold cyan]")
    console.print("─" * 50)

    # Try to find and show manuscript config
    if config_exists_quietly():
        try:
            config_manager = get_config_manager()
            with suppress_stderr():
                config = config_manager.load_config()

            # Show key fields in table format
            table = Table(show_header=False, box=None)
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("Title", config.get("title", "Not set"))
            table.add_row("Authors", str(len(config.get("authors", []))))
            output_format = config.get("output", {}).get("format", "pdf")
            table.add_row("Output format", output_format)

            console.print(table)
        except Exception:
            console.print("[dim]No manuscript config found in current directory[/dim]")
    else:
        console.print("[dim]No manuscript config found in current directory[/dim]")

    console.print("\n[bold cyan]Global Repository Configuration[/bold cyan]")
    console.print("─" * 50)

    # Show repo config
    repo_config = get_repo_config()
    config_data = repo_config.show()

    table = Table(show_header=False, box=None)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Parent Directory", str(config_data.get("repo_parent_dir", "Not set")))
    table.add_row("Expanded Path", str(config_data.get("repo_parent_dir_expanded", "N/A")))

    if config_data.get("repo_default_github_org"):
        table.add_row("Default GitHub Org", config_data["repo_default_github_org"])
    else:
        table.add_row("Default GitHub Org", "[dim]Not set[/dim]")

    if config_data.get("repo_default_editor"):
        table.add_row("Default Editor", config_data["repo_default_editor"])

    table.add_row("Config File", str(repo_config.config_path))

    console.print(table)
    console.print()


def run_interactive_config_menu():
    """Run the interactive configuration menu."""
    # Menu action registry - maps choice numbers to handler functions
    menu_actions = {
        "1": handle_view_manuscript_config,
        "2": handle_init_manuscript_config,
        "3": handle_validate_manuscript_config,
        "4": handle_edit_manuscript_value,
        "5": handle_export_manuscript_config,
        "6": handle_view_repositories,
        "7": handle_set_repo_parent_dir,
        "8": handle_set_repo_org,
        "9": handle_set_repo_editor,
        "10": handle_list_config_files,
    }

    while True:
        try:
            display_config_menu()

            from prompt_toolkit.completion import WordCompleter

            max_choice = len(menu_actions) + 1  # +1 for exit option
            choice = prompt_text(
                f"\nEnter choice (1-{max_choice}): ",
                completer=WordCompleter([str(i) for i in range(1, max_choice + 1)]),
            )

            choice = choice.strip()

            # Check for exit
            if choice == str(max_choice):
                console.print("\n[green]✓ Exiting configuration menu.[/green]\n")
                break

            # Dispatch to handler
            handler = menu_actions.get(choice)
            if handler:
                handler()
            else:
                console.print(f"[red]Invalid choice: {choice}. Please enter 1-{max_choice}.[/red]")

        except (KeyboardInterrupt, EOFError):
            console.print("\n[green]✓ Configuration saved. Exiting.[/green]\n")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def display_config_menu():
    """Display the interactive configuration menu."""
    # Load current configurations
    repo_config = get_repo_config()

    console.print("\n" + "=" * 60)
    console.print("[bold cyan]rxiv-maker Configuration Menu[/bold cyan]")
    console.print("=" * 60)

    # Show current configuration
    console.print("\n[bold green]CURRENT CONFIGURATION[/bold green]")
    console.print("─" * 60)

    # Manuscript config (in current directory)
    console.print("[yellow]Manuscript Config (in current directory):[/yellow]")

    # Check if we're in a manuscript directory first (to avoid error messages)
    if config_exists_quietly():
        try:
            config_manager = get_config_manager()
            with suppress_stderr():
                config = config_manager.load_config()
                config_file = config_manager._find_existing_config()

            if config_file:
                console.print(f"  [green]✓[/green] Config found: {config_file.name}")
                console.print(f"  Title: {config.get('title', 'Not set')}")
                console.print(f"  Authors: {len(config.get('authors', []))} authors")
                console.print(f"  Output format: {config.get('output', {}).get('format', 'pdf')}")
        except Exception:
            console.print("  [dim]No config file found[/dim]")
    else:
        console.print("  [dim]No config file found[/dim]")

    # Repository config (global)
    console.print("\n[yellow]Global Repository Config (~/.rxiv-maker/config):[/yellow]")
    config_data = repo_config.show()
    console.print(f"  Parent directory: {config_data.get('repo_parent_dir', 'Not set')}")

    if config_data.get("repo_default_github_org"):
        console.print(f"  Default GitHub org: {config_data['repo_default_github_org']}")

    if config_data.get("repo_default_editor"):
        console.print(f"  Default editor: {config_data['repo_default_editor']}")

    # Menu options
    console.print("\n[bold green]CONFIGURATION OPTIONS[/bold green]")
    console.print("─" * 60)

    console.print("[yellow]Manuscript Configuration:[/yellow]")
    console.print("  1. View current manuscript config")
    console.print("  2. Initialize manuscript config from template")
    console.print("  3. Validate manuscript config")
    console.print("  4. Edit manuscript config value")
    console.print("  5. Export manuscript config")

    console.print("\n[yellow]Repository Configuration:[/yellow]")
    console.print("  6. View all manuscript repositories")
    console.print("  7. Set parent directory for repositories")
    console.print("  8. Set default GitHub organization")
    console.print("  9. Set default editor")

    console.print("\n[yellow]Other:[/yellow]")
    console.print("  10. List all config files")
    console.print("  11. Exit")


# ============================================================================
# Menu Action Handlers
# ============================================================================


def handle_view_manuscript_config():
    """Handle viewing manuscript configuration."""
    console.print("\n[cyan]Viewing manuscript configuration...[/cyan]\n")

    # Check if config exists first
    if not config_exists_quietly():
        console.print("[yellow]No manuscript config found in current directory[/yellow]")
        console.print("\nTip: Run 'rxiv config init' or navigate to a manuscript directory")
        return

    try:
        config_manager = get_config_manager()
        with suppress_stderr():
            config = config_manager.load_config()

        import yaml

        console.print(yaml.dump(config, default_flow_style=False, sort_keys=False))
        console.print("[green]✓ Configuration displayed[/green]")
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")


def handle_init_manuscript_config():
    """Handle initializing manuscript configuration."""
    console.print("\n[cyan]Initialize manuscript configuration[/cyan]\n")

    try:
        from ..interactive_prompts import prompt_template_choice, prompt_yes_no

        # Ask for template
        console.print("Available templates: default, minimal, journal, preprint")
        template = prompt_template_choice(default="default")

        # Check if config exists
        config_manager = get_config_manager()
        config_file = config_manager._find_existing_config()

        if config_file and config_file.exists():
            console.print(f"\n[yellow]Warning: Config file already exists: {config_file}[/yellow]")
            if not prompt_yes_no("Overwrite existing config?", default=False):
                console.print("[yellow]Cancelled[/yellow]")
                return

        # Initialize config
        config_path = config_manager.init_config(template=template, force=True)
        console.print(f"\n[green]✓ Created configuration file: {config_path}[/green]")

    except Exception as e:
        console.print(f"[red]Error initializing config: {e}[/red]")


def handle_validate_manuscript_config():
    """Handle validating manuscript configuration."""
    console.print("\n[cyan]Validating manuscript configuration...[/cyan]\n")

    # Check if config exists first
    if not config_exists_quietly():
        console.print("[yellow]No manuscript config found in current directory[/yellow]")
        console.print("\nTip: Run 'rxiv init' to initialize a manuscript or navigate to a manuscript directory")
        return

    try:
        config_manager = get_config_manager()
        with suppress_stderr():
            result = config_manager.validate_config()

        if result.get("valid"):
            console.print("[green]✓ Configuration is valid[/green]")
        else:
            console.print("[red]✗ Configuration has errors:[/red]")
            for error in result.get("errors", []):
                console.print(f"  - {error}")

        warnings = result.get("warnings", [])
        if warnings:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in warnings:
                console.print(f"  - {warning}")

    except Exception as e:
        console.print(f"[red]Error validating config: {e}[/red]")


def handle_edit_manuscript_value():
    """Handle editing a manuscript configuration value."""
    console.print("\n[cyan]Edit manuscript configuration value[/cyan]\n")

    # Check if config exists first
    if not config_exists_quietly():
        console.print("[yellow]No manuscript config found in current directory[/yellow]")
        console.print("\nTip: Run 'rxiv init' to initialize a manuscript or navigate to a manuscript directory")
        return

    try:
        from ..interactive_prompts import prompt_config_key

        # Get available keys from current config
        config_manager = get_config_manager()
        with suppress_stderr():
            config = config_manager.load_config()

        available_keys = list(config.keys())
        console.print(f"Available keys: {', '.join(available_keys)}")

        key = prompt_config_key(available_keys)

        console.print(f"\nCurrent value: {config.get(key, 'Not set')}")

        new_value = prompt_text(f"New value for '{key}': ")

        # Simple string update (for more complex updates, user should edit file directly)
        config_manager.set_config_value(key, new_value)

        console.print(f"\n[green]✓ Updated {key}[/green]")

    except Exception as e:
        console.print(f"[red]Error editing config: {e}[/red]")


def handle_export_manuscript_config():
    """Handle exporting manuscript configuration."""
    console.print("\n[cyan]Export manuscript configuration[/cyan]\n")

    # Check if config exists first
    if not config_exists_quietly():
        console.print("[yellow]No manuscript config found in current directory[/yellow]")
        console.print("\nTip: Run 'rxiv init' to initialize a manuscript or navigate to a manuscript directory")
        return

    try:
        from ..interactive_prompts import prompt_path

        output_path = prompt_path(
            "Export to: ",
            default="config-export.yml",
            must_exist=False,
            must_be_dir=False,
        )

        config_manager = get_config_manager()
        config_manager.export_config(output_path, format_type="yaml")

        console.print(f"\n[green]✓ Exported configuration to: {output_path}[/green]")

    except Exception as e:
        console.print(f"[red]Error exporting config: {e}[/red]")


def handle_view_repositories():
    """Handle viewing all manuscript repositories."""
    console.print("\n[cyan]Viewing manuscript repositories...[/cyan]\n")

    try:
        repo_config = get_repo_config()
        repo_manager = RepositoryManager(repo_config)

        repos = repo_manager.discover_repositories()

        if not repos:
            console.print(f"[yellow]No manuscript repositories found in: {repo_config.parent_dir}[/yellow]")
            console.print("\nCreate a repository with: rxiv create-repo NAME")
            return

        table = Table(title=f"Manuscript Repositories in {repo_config.parent_dir}")
        table.add_column("Name", style="bold cyan")
        table.add_column("Path", style="dim")
        table.add_column("Status")

        for repo in repos:
            status = "[green]✓ MANUSCRIPT[/green]" if repo.has_manuscript_dir() else "[red]✗ No MANUSCRIPT[/red]"
            table.add_row(repo.name, str(repo.path), status)

        console.print(table)
        console.print(f"\n[green]✓ Found {len(repos)} repositories[/green]")

    except Exception as e:
        console.print(f"[red]Error listing repositories: {e}[/red]")


def handle_set_repo_parent_dir():
    """Handle setting repository parent directory."""
    console.print("\n[cyan]Set repository parent directory[/cyan]\n")

    try:
        from ..interactive_prompts import prompt_yes_no

        repo_config = get_repo_config()
        current = str(repo_config.parent_dir)

        console.print(f"Current parent directory: {current}")

        new_path = prompt_path(
            "New parent directory: ",
            default=current,
            must_exist=False,
            must_be_dir=True,
        )

        # Create if doesn't exist
        if not new_path.exists():
            if prompt_yes_no("Directory does not exist. Create it?", default=True):
                new_path.mkdir(parents=True, exist_ok=True)
                console.print(f"[green]✓[/green] Created directory: {new_path}")

        repo_config.parent_dir = str(new_path)
        console.print(f"\n[green]✓ Set repository parent directory to: {new_path}[/green]")

    except Exception as e:
        console.print(f"[red]Error setting parent directory: {e}[/red]")


def handle_set_repo_org():
    """Handle setting default GitHub organization."""
    console.print("\n[cyan]Set default GitHub organization[/cyan]\n")

    try:
        from ...utils.github import GitHubError, get_github_orgs

        repo_config = get_repo_config()
        current = repo_config.default_github_org

        console.print(f"Current GitHub organization: {current or 'Not set'}")

        # Try to fetch available orgs
        existing_orgs = None
        try:
            existing_orgs = get_github_orgs()
            if existing_orgs:
                console.print(f"Available organizations: {', '.join(existing_orgs)}")
        except GitHubError:
            console.print("[dim]Could not fetch GitHub organizations (gh CLI not authenticated)[/dim]")

        new_org = prompt_github_org(
            "New GitHub organization: ",
            default=current,
            existing_orgs=existing_orgs,
        )

        if new_org:
            repo_config.default_github_org = new_org
            console.print(f"\n[green]✓ Set default GitHub organization to: {new_org}[/green]")
        else:
            console.print("[yellow]Cancelled (empty value)[/yellow]")

    except Exception as e:
        console.print(f"[red]Error setting GitHub organization: {e}[/red]")


def handle_set_repo_editor():
    """Handle setting default editor."""
    console.print("\n[cyan]Set default editor[/cyan]\n")

    try:
        repo_config = get_repo_config()
        current = repo_config.default_editor

        console.print(f"Current editor: {current or 'Not set'}")

        new_editor = prompt_editor(
            "New default editor: ",
            default=current,
        )

        if new_editor:
            repo_config.default_editor = new_editor
            console.print(f"\n[green]✓ Set default editor to: {new_editor}[/green]")
        else:
            console.print("[yellow]Cancelled (empty value)[/yellow]")

    except Exception as e:
        console.print(f"[red]Error setting editor: {e}[/red]")


def handle_list_config_files():
    """Handle listing all config files."""
    console.print("\n[cyan]Listing configuration files...[/cyan]\n")

    try:
        from pathlib import Path

        files = []

        # Check for global repository config first
        repo_config = get_repo_config()
        repo_config_path = repo_config.config_path
        # Add .yaml extension for display (actual file has no extension)
        repo_config_display = f"{repo_config_path}.yaml"
        if repo_config_path.exists():
            stat = repo_config_path.stat()
            files.append(
                {
                    "path": repo_config_display,
                    "exists": True,
                    "size": stat.st_size,
                    "type": "Repository",
                    "repo_name": "-",
                }
            )
        else:
            files.append(
                {
                    "path": repo_config_display,
                    "exists": False,
                    "size": 0,
                    "type": "Repository",
                    "repo_name": "-",
                }
            )

        # Discover all manuscript repositories
        repo_manager = RepositoryManager()
        try:
            parent_dir = repo_config.parent_dir
            if parent_dir.exists():
                repos = repo_manager.discover_repositories(parent_dir)

                # Add config file for each repository
                for repo in repos:
                    manuscript_config = repo.manuscript_dir / "00_CONFIG.yml"
                    if manuscript_config.exists():
                        stat = manuscript_config.stat()
                        files.append(
                            {
                                "path": str(manuscript_config),
                                "exists": True,
                                "size": stat.st_size,
                                "type": "Manuscript",
                                "repo_name": repo.name,
                            }
                        )
                    else:
                        files.append(
                            {
                                "path": str(manuscript_config),
                                "exists": False,
                                "size": 0,
                                "type": "Manuscript",
                                "repo_name": repo.name,
                            }
                        )
        except Exception:
            # If no parent dir configured or error, just show current directory
            manuscript_config = Path.cwd() / "00_CONFIG.yml"
            if manuscript_config.exists():
                stat = manuscript_config.stat()
                files.append(
                    {
                        "path": str(manuscript_config),
                        "exists": True,
                        "size": stat.st_size,
                        "type": "Manuscript",
                        "repo_name": "current",
                    }
                )
            else:
                files.append(
                    {
                        "path": str(manuscript_config),
                        "exists": False,
                        "size": 0,
                        "type": "Manuscript",
                        "repo_name": "current",
                    }
                )

        table = Table(title="Configuration Files", expand=True)
        table.add_column("Type", style="yellow", no_wrap=True)
        table.add_column("Repo", style="magenta", no_wrap=True)
        table.add_column("Path", style="cyan", overflow="fold")
        table.add_column("Exists", justify="center", no_wrap=True)
        table.add_column("Size", no_wrap=True)

        for file_info in files:
            exists = "[green]✓[/green]" if file_info["exists"] else "[red]✗[/red]"
            size = f"{file_info.get('size', 0)} bytes" if file_info["exists"] else "-"
            table.add_row(file_info["type"], file_info["repo_name"], file_info["path"], exists, size)

        console.print(table)
        console.print()
        console.print(f"[dim]Found {len([f for f in files if f['type'] == 'Manuscript'])} manuscript config(s)[/dim]")
        console.print("[dim]Manuscript configs: */MANUSCRIPT/00_CONFIG.yml in each repository[/dim]")
        console.print("[dim]Repository config: ~/.rxiv-maker/config for global settings[/dim]")
        console.print()

    except Exception as e:
        console.print(f"[red]Error listing files: {e}[/red]")
