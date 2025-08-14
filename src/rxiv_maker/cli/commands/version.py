"""Version command for rxiv-maker CLI."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ... import __version__
from ...utils.platform import platform_detector
from ...utils.update_checker import force_update_check

console = Console()


@click.command()
@click.option("--detailed", "-d", is_flag=True, help="Show detailed version information")
@click.option("--check-updates", "-u", is_flag=True, help="Check for available updates")
@click.pass_context
def version(ctx: click.Context, detailed: bool, check_updates: bool) -> None:
    """Show version information."""
    # Check for updates if requested
    if check_updates:
        try:
            console.print("🔍 Checking for updates...", style="blue")
        except UnicodeEncodeError:
            try:
                console.print("[CHECKING] Checking for updates...", style="blue")
            except UnicodeEncodeError:
                print("Checking for updates...")
        try:
            update_available, latest_version = force_update_check()
            if update_available:
                try:
                    console.print(
                        f"📦 Update available: {__version__} → {latest_version}",
                        style="green",
                    )
                except UnicodeEncodeError:
                    try:
                        console.print(
                            f"[UPDATE] Update available: {__version__} → {latest_version}",
                            style="green",
                        )
                    except UnicodeEncodeError:
                        print(f"Update available: {__version__} → {latest_version}")

                try:
                    console.print("   Run: pip install --upgrade rxiv-maker", style="blue")
                    console.print(
                        f"   Release notes: https://github.com/henriqueslab/rxiv-maker/releases/tag/v{latest_version}",
                        style="blue",
                    )
                except UnicodeEncodeError:
                    print("   Run: pip install --upgrade rxiv-maker")
                    print(
                        f"   Release notes: https://github.com/henriqueslab/rxiv-maker/releases/tag/v{latest_version}"
                    )
            else:
                try:
                    console.print(f"✅ You have the latest version ({__version__})", style="green")
                except UnicodeEncodeError:
                    try:
                        console.print(
                            f"[OK] You have the latest version ({__version__})",
                            style="green",
                        )
                    except UnicodeEncodeError:
                        print(f"You have the latest version ({__version__})")
        except Exception as e:
            try:
                console.print(f"❌ Could not check for updates: {e}", style="red")
            except UnicodeEncodeError:
                try:
                    console.print(f"[ERROR] Could not check for updates: {e}", style="red")
                except UnicodeEncodeError:
                    print(f"Could not check for updates: {e}")

        try:
            console.print()  # Add spacing
        except UnicodeEncodeError:
            print()  # Add spacing

    if detailed:
        # Create detailed version table
        table = Table(title="Rxiv-Maker Version Information")
        table.add_column("Component", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Status", style="yellow")

        # Add version info
        table.add_row("Rxiv-Maker", __version__, "✅ Installed")

        # Add platform info
        table.add_row("Platform", platform_detector.platform, "✅ Detected")
        table.add_row("Python", f"{sys.version.split()[0]}", "✅ Compatible")

        # Add dependency info
        try:
            import click

            table.add_row("Click", str(click.__version__), "✅ Available")
        except ImportError:
            table.add_row("Click", "Not found", "❌ Missing")

        try:
            # Rich doesn't have __version__, try getting it from metadata
            try:
                import importlib.metadata

                rich_version = importlib.metadata.version("rich")
                table.add_row("Rich", rich_version, "✅ Available")
            except (ImportError, importlib.metadata.PackageNotFoundError):
                table.add_row("Rich", "Available", "✅ Available")
        except ImportError:
            table.add_row("Rich", "Not found", "❌ Missing")

        try:
            import matplotlib

            table.add_row("Matplotlib", matplotlib.__version__, "✅ Available")
        except ImportError:
            table.add_row("Matplotlib", "Not found", "❌ Missing")

        try:
            console.print(table)

            # Show additional info
            install_path = Path(__file__).parent.parent.parent.absolute()
            console.print(
                f"\n📁 Installation path: {install_path}",
                style="blue",
            )
            console.print(f"🐍 Python executable: {sys.executable}", style="blue")
        except UnicodeEncodeError:
            # Fallback for Windows environments with limited encoding
            try:
                console.print(table)
                install_path = Path(__file__).parent.parent.parent.absolute()
                console.print(
                    f"\n[PATH] Installation path: {install_path}",
                    style="blue",
                )
                console.print(f"[PYTHON] Python executable: {sys.executable}", style="blue")
            except UnicodeEncodeError:
                # Final fallback - use plain print
                print("\nRxiv-Maker Version Information")
                print("=" * 50)
                print(f"Rxiv-Maker: {__version__} (Installed)")
                print(f"Platform: {platform_detector.platform} (Detected)")
                print(f"Python: {sys.version.split()[0]} (Compatible)")

                # Add dependency info
                try:
                    import click

                    print(f"Click: {click.__version__} (Available)")
                except ImportError:
                    print("Click: Not found (Missing)")

                try:
                    import importlib.metadata

                    rich_version = importlib.metadata.version("rich")
                    print(f"Rich: {rich_version} (Available)")
                except (ImportError, importlib.metadata.PackageNotFoundError):
                    print("Rich: Available (Available)")

                try:
                    import matplotlib

                    print(f"Matplotlib: {matplotlib.__version__} (Available)")
                except ImportError:
                    print("Matplotlib: Not found (Missing)")

                install_path = Path(__file__).parent.parent.parent.absolute()
                print(f"\nInstallation path: {install_path}")
                print(f"Python executable: {sys.executable}")

    else:
        # Simple version output
        try:
            console.print(f"rxiv-maker {__version__}", style="green")
        except UnicodeEncodeError:
            print(f"rxiv-maker {__version__}")
