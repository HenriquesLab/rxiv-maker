"""Rich console adapter for upgrade notifications in rxiv-maker."""

import click
from rich.console import Console


class RxivUpgradeNotifier:
    """Adapt Rich console to UpgradeNotifier protocol for rxiv-maker.

    Integrates with rxiv-maker's changelog parser to show rich change summaries.
    """

    def __init__(self, console: Console):
        """Initialize with Rich console instance.

        Args:
            console: Rich Console instance for styled output
        """
        self.console = console

    def show_checking(self) -> None:
        """Show 'checking for updates' message."""
        self.console.print("🔍 Checking for updates...", style="blue")

    def show_version_check(self, current: str, latest: str, available: bool) -> None:
        """Show version check results.

        Args:
            current: Current installed version
            latest: Latest available version
            available: Whether an update is available
        """
        if available:
            self.console.print(
                f"📦 Update available: [cyan]v{current}[/cyan] → [green bold]v{latest}[/green bold]",
                style="yellow",
            )
        else:
            self.console.print(
                f"✅ You already have the latest version ([cyan]v{current}[/cyan])",
                style="green",
            )

    def show_update_info(self, current: str, latest: str, release_url: str) -> None:
        """Show update available information with changelog integration.

        Args:
            current: Current version
            latest: Latest version
            release_url: URL to release notes
        """
        # Import here to avoid circular dependencies
        from .changelog_parser import fetch_and_format_changelog

        # Fetch and display changelog
        summary, error = fetch_and_format_changelog(
            current_version=current,
            latest_version=latest,
            highlights_per_version=3,
        )

        if summary and not error:
            self.console.print("\n📋 What's changing:", style="bold blue")
            # Display changelog - format_summary returns rich-formatted text
            # Parse and display with proper styling
            for line in summary.split("\n"):
                if line.startswith("⚠️"):
                    # Highlight breaking changes prominently
                    self.console.print(line, style="bold red")
                elif "What's New:" in line or "What's changing:" in line:
                    self.console.print(line, style="bold cyan")
                elif line.strip().startswith("v"):
                    # Version headers
                    self.console.print(line, style="bold yellow")
                elif line.strip().startswith(("✨", "🔄", "🐛", "🗑️", "🔒", "📝")):
                    # Change items with emojis
                    self.console.print(f"   {line.strip()}", style="white")
                elif line.strip().startswith("•"):
                    # Breaking change items
                    self.console.print(f"   {line.strip()}", style="yellow")
                elif line.strip():
                    self.console.print(f"   {line}", style="dim")
        else:
            # Fallback if changelog unavailable
            self.console.print(
                f"\nView release notes: [link]{release_url}[/link]",
                style="blue",
            )

    def show_installer_info(self, friendly_name: str, command: str) -> None:
        """Show detected installer information.

        Args:
            friendly_name: Human-readable installer name
            command: The upgrade command that will be executed
        """
        self.console.print()
        self.console.print(
            f"🔍 Detected installation method: [bold]{friendly_name}[/bold]",
            style="blue",
        )
        self.console.print(f"📦 Running: [yellow]{command}[/yellow]")

    def show_success(self, version: str) -> None:
        """Show successful upgrade message.

        Args:
            version: Version that was successfully installed
        """
        self.console.print()
        self.console.print("✅ Upgrade completed successfully!", style="green bold")
        self.console.print(f"   Now running: [green]v{version}[/green]")
        self.console.print()
        self.console.print("   Run [blue]'rxiv --version'[/blue] to verify the installation", style="dim")

    def show_error(self, error: str | None) -> None:
        """Show upgrade error message.

        Args:
            error: Error message or None
        """
        self.console.print()
        self.console.print("❌ Upgrade failed", style="red bold")
        if error:
            self.console.print(f"   {error}", style="red")

    def show_manual_instructions(self, install_method: str) -> None:
        """Show manual upgrade instructions.

        Args:
            install_method: The detected installation method
        """
        self.console.print("\n💡 Try running manually:", style="yellow bold")

        if install_method == "homebrew":
            self.console.print("   [cyan]brew update && brew upgrade rxiv-maker[/cyan]")
        elif install_method == "pipx":
            self.console.print("   [cyan]pipx upgrade rxiv-maker[/cyan]")
        elif install_method == "uv":
            self.console.print("   [cyan]uv tool upgrade rxiv-maker[/cyan]")
        elif install_method == "dev":
            self.console.print("   [cyan]cd <repo> && git pull && uv sync[/cyan]", style="dim")
        else:
            self.console.print("   [cyan]pip install --upgrade rxiv-maker[/cyan]")
            self.console.print("   [dim]# Or with --user flag:[/dim]")
            self.console.print("   [cyan]pip install --upgrade --user rxiv-maker[/cyan]")

    def confirm_upgrade(self, version: str) -> bool:
        """Prompt user for confirmation using click.

        Args:
            version: Version to upgrade to

        Returns:
            True if user confirms, False otherwise
        """
        try:
            self.console.print()
            return click.confirm(f"Upgrade rxiv-maker to v{version}?", default=True)
        except (KeyboardInterrupt, EOFError):
            self.console.print("\n⚠️  Upgrade cancelled.", style="yellow")
            return False
