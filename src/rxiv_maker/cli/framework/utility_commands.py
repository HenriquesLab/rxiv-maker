"""Utility command implementations for rxiv-maker CLI."""

import json
import platform
import sys
from pathlib import Path
from typing import Optional

import click
from rich.panel import Panel
from rich.table import Table

from .base import BaseCommand, CommandExecutionError


class CheckInstallationCommand(BaseCommand):
    """Check installation command implementation using the framework."""

    def execute_operation(self, detailed: bool = False, fix: bool = False, json_output: bool = False) -> None:
        """Execute installation check using the new dependency manager.

        Args:
            detailed: Show detailed diagnostic information
            fix: Attempt to fix missing dependencies
            json_output: Output results in JSON format
        """
        import platform

        from ...core.managers.dependency_manager import get_dependency_manager

        dm = get_dependency_manager()
        current_platform = platform.system()

        if json_output:
            # Check all dependencies and format as JSON
            all_missing = dm.get_missing_dependencies()
            pdf_missing = dm.get_missing_dependencies("pdf", required_only=True)

            components = {}
            ubuntu_packages = []

            for result in all_missing:
                components[result.spec.name] = {
                    "type": result.spec.type.value,
                    "status": result.status.value,
                    "required": result.spec.required,
                    "contexts": list(result.spec.contexts),
                    "resolution_hint": result.resolution_hint,
                }

                if result.spec.type.value == "ubuntu_package" and result.spec.required:
                    ubuntu_packages.append(result.spec.name)

            output = {
                "status": "complete" if not pdf_missing else "incomplete",
                "platform": current_platform,
                "total_dependencies": len(dm.dependencies),
                "missing_required_for_pdf": len(pdf_missing),
                "missing_components": components,
                "ubuntu_install_command": f"sudo apt install -y {' '.join(ubuntu_packages)}"
                if ubuntu_packages and current_platform == "Linux"
                else None,
                "summary": {
                    "total_missing": len(all_missing),
                    "critical_missing": len(pdf_missing),
                    "ubuntu_packages_missing": len(ubuntu_packages),
                },
            }

            self.console.print(json.dumps(output, indent=2))
            return

        self.console.print(Panel.fit("🔍 Checking rxiv-maker Dependencies", style="blue"))

        with self.create_progress() as progress:
            task = progress.add_task("Checking dependencies...", total=None)

            try:
                # Check PDF dependencies (most critical)
                pdf_missing = dm.get_missing_dependencies("pdf", required_only=True)
                all_missing = dm.get_missing_dependencies() if detailed else pdf_missing

                progress.update(task, description="✅ Dependency check completed")

                if detailed:
                    self._show_detailed_dependency_results(dm, all_missing)
                else:
                    self._show_basic_dependency_results(pdf_missing)

                # Show platform-specific installation instructions
                if pdf_missing and current_platform == "Linux":
                    ubuntu_packages = [r.spec.name for r in pdf_missing if r.spec.type.value == "ubuntu_package"]
                    if ubuntu_packages:
                        self.console.print("\n📦 Ubuntu installation command:", style="blue")
                        self.console.print(f"sudo apt install -y {' '.join(ubuntu_packages)}", style="green")

                if pdf_missing:
                    if fix and current_platform == "Linux":
                        self.console.print("\n🔧 Attempting to install missing dependencies...")
                        success = dm.install_missing_dependencies("pdf", interactive=False)
                        if success:
                            self.success_message("Dependencies installed successfully!")
                        else:
                            self.error_message("Some dependencies could not be installed automatically")
                    else:
                        self.console.print(
                            f"\n⚠️  {len(pdf_missing)} required dependencies missing for PDF generation", style="yellow"
                        )
                        if current_platform == "Linux":
                            self.console.print("💡 Run with --fix to attempt automatic installation", style="blue")
                else:
                    self.success_message("All required dependencies for PDF generation are available!")

                # Show next steps
                self._show_dependency_next_steps(pdf_missing)

            except Exception as e:
                progress.update(task, description="❌ Dependency check failed")
                self.error_message(f"Dependency check failed: {e}")
                raise CommandExecutionError(f"Dependency check failed: {e}") from e

    def _show_basic_dependency_results(self, missing_results: list) -> None:
        """Show basic dependency results using the new dependency manager."""
        if not missing_results:
            self.console.print("✅ All required dependencies are available!", style="green")
            return

        table = Table(title="Missing Required Dependencies", show_header=True, header_style="bold red")
        table.add_column("Component", style="cyan", width=25)
        table.add_column("Type", style="yellow", width=15)
        table.add_column("Installation", style="green")

        for result in missing_results:
            table.add_row(
                result.spec.name,
                result.spec.type.value.replace("_", " ").title(),
                result.resolution_hint or "Manual installation required",
            )

        self.console.print(table)

    def _show_detailed_dependency_results(self, dm, all_missing: list) -> None:
        """Show detailed dependency results."""
        # Show summary first
        total_deps = len(dm.dependencies)
        missing_count = len(all_missing)

        self.console.print(
            f"\n📊 Summary: {missing_count} missing out of {total_deps} total dependencies", style="blue"
        )

        if not all_missing:
            self.console.print("✅ All dependencies are available!", style="green")
            return

        # Group by type
        by_type = {}
        for result in all_missing:
            dep_type = result.spec.type.value
            if dep_type not in by_type:
                by_type[dep_type] = []
            by_type[dep_type].append(result)

        for dep_type, results in by_type.items():
            table = Table(
                title=f"Missing {dep_type.replace('_', ' ').title()} Dependencies",
                show_header=True,
                header_style="bold yellow",
            )
            table.add_column("Name", style="cyan", width=25)
            table.add_column("Required", width=10)
            table.add_column("Contexts", width=20)
            table.add_column("Installation", style="green")

            for result in results:
                table.add_row(
                    result.spec.name,
                    "✅ Yes" if result.spec.required else "⚠️ Optional",
                    ", ".join(result.spec.contexts) if result.spec.contexts else "all",
                    result.resolution_hint or "Manual installation required",
                )

            self.console.print(table)
            self.console.print()

    def _show_dependency_next_steps(self, missing_results: list) -> None:
        """Show next steps after dependency check."""
        if not missing_results:
            self.console.print("\n🚀 Next steps:", style="blue")
            self.console.print("  • Test PDF generation: rxiv pdf ../manuscript-rxiv-maker/MANUSCRIPT")
            return

        self.console.print("\n🔧 Next steps:", style="blue")
        self.console.print("  • Install missing dependencies shown above")
        self.console.print("  • Re-run: rxiv check-installation")
        self.console.print("  • Test PDF generation: rxiv pdf ../manuscript-rxiv-maker/MANUSCRIPT")

    def _show_basic_results(self, results: dict) -> None:
        """Show basic installation results."""
        table = Table(title="Installation Status", show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan", width=20)
        table.add_column("Status", width=15)
        table.add_column("Notes", style="dim")

        component_names = {
            "python": "Python",
            "pip": "pip",
            "latex": "LaTeX",
            "pandoc": "Pandoc",
            "r": "R (Optional)",
            "nodejs": "Node.js",
        }

        for component, installed in results.items():
            name = component_names.get(component, component.title())
            status = "✅ Installed" if installed else "❌ Missing"
            style = "green" if installed else "red"
            notes = ""

            if component == "r" and not installed:
                notes = "Optional for R figure scripts"
                style = "yellow"

            table.add_row(name, status, notes, style=style)

        self.console.print(table)

    def _show_detailed_results(self, results: dict) -> None:
        """Show detailed installation results."""
        # Show basic results first
        self._show_basic_results(results)

        # Add detailed diagnostics
        self.console.print("\n🔍 Detailed Diagnostics:")
        try:
            from rxiv_maker.install.utils.verification import diagnose_installation

            diagnosis = diagnose_installation()
            for component, details in diagnosis.items():
                if isinstance(details, dict):
                    self.console.print(f"\n[bold cyan]{component.title()}:[/bold cyan]")
                    for key, value in details.items():
                        self.console.print(f"  {key}: {value}")
                else:
                    self.console.print(f"{component}: {details}")
        except Exception as e:
            self.console.print(f"[yellow]Could not get detailed diagnostics: {e}[/yellow]")

    def _fix_missing_dependencies(self, missing_components: list) -> None:
        """Attempt to fix missing dependencies."""
        # Check if we're on a supported platform for automatic fixing
        system = platform.system().lower()
        if system != "linux":
            self.console.print("🚧 Automatic fixing only supported on Linux", style="yellow")
            self._show_manual_install_instructions(missing_components)
            return

        # Check if we can detect Ubuntu/Debian
        try:
            with open("/etc/os-release", "r") as f:
                os_info = f.read()
            is_ubuntu = any(distro in os_info.lower() for distro in ["ubuntu", "debian", "mint"])
        except (FileNotFoundError, IOError, OSError):
            is_ubuntu = False

        if not is_ubuntu:
            self.console.print("🚧 Automatic fixing only supported on Ubuntu/Debian", style="yellow")
            self._show_manual_install_instructions(missing_components)
            return

        # Install critical missing components
        success_count = 0
        for component in missing_components:
            if component == "latex":
                if self._install_latex_ubuntu():
                    success_count += 1
            # Add other critical components here if needed in the future

        # Ask about optional R installation if not already installed
        try:
            from rxiv_maker.install.utils.verification import verify_installation

            current_status = verify_installation(verbose=False)
            if not current_status.get("r", False):
                install_r = click.confirm("\n🤔 Would you like to install R? (optional for R figure scripts)")
                if install_r and self._install_r_ubuntu():
                    success_count += 1
        except Exception:
            pass  # Skip R installation prompt if verification fails

        if success_count > 0:
            self.console.print(f"\n✅ Successfully installed {success_count} components!", style="green")
            self.console.print("💡 Run 'rxiv check-installation' again to verify", style="blue")
        else:
            self.console.print("\n⚠️ Could not install components automatically", style="yellow")
            self._show_manual_install_instructions(missing_components)

    def _install_latex_ubuntu(self) -> bool:
        """Install LaTeX on Ubuntu/Debian."""
        import subprocess

        try:
            self.console.print("🔧 Installing LaTeX (this may take several minutes)...", style="blue")

            cmd = (
                "apt update && "
                "apt install -y texlive-latex-base texlive-latex-recommended "
                "texlive-latex-extra texlive-fonts-recommended texlive-fonts-extra "
                "texlive-bibtex-extra texlive-science biber"
            )

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=1200)

            if result.returncode == 0:
                self.console.print("✅ Successfully installed LaTeX", style="green")
                return True
            else:
                self.console.print(f"❌ Failed to install LaTeX: {result.stderr[:500]}", style="red")
                return False

        except subprocess.TimeoutExpired:
            self.console.print("⏰ LaTeX installation timed out (try manually)", style="yellow")
            return False
        except Exception as e:
            self.console.print(f"❌ Error installing LaTeX: {e}", style="red")
            return False

    def _install_r_ubuntu(self) -> bool:
        """Install R on Ubuntu/Debian."""
        import subprocess

        try:
            self.console.print("🔧 Installing R...", style="blue")

            cmd = "apt update && apt install -y r-base"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                self.console.print("✅ Successfully installed R", style="green")
                return True
            else:
                self.console.print(f"❌ Failed to install R: {result.stderr[:500]}", style="red")
                return False

        except subprocess.TimeoutExpired:
            self.console.print("⏰ R installation timed out", style="yellow")
            return False
        except Exception as e:
            self.console.print(f"❌ Error installing R: {e}", style="red")
            return False

    def _show_manual_install_instructions(self, missing_components: list) -> None:
        """Show manual installation instructions for missing components."""
        system = platform.system().lower()
        self.console.print("\n📦 Manual Installation Instructions:", style="bold blue")

        for component in missing_components:
            if component == "latex":
                if system == "linux":
                    self.console.print("  • LaTeX (Ubuntu/Debian):")
                    self.console.print(
                        "    sudo apt update && sudo apt install -y texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-science"
                    )
                elif system == "darwin":
                    self.console.print("  • LaTeX (macOS):")
                    self.console.print("    brew install --cask mactex")
                    self.console.print("    # OR install BasicTeX: brew install --cask basictex")
                else:
                    self.console.print("  • LaTeX: Install TeX Live distribution for your platform")

            elif component == "system_libs":
                self.console.print("  • Python Libraries:")
                self.console.print("    pip install matplotlib numpy pillow pandas scipy")

            elif component == "r":
                if system == "linux":
                    self.console.print("  • R (Ubuntu/Debian, optional):")
                    self.console.print("    sudo apt install -y r-base")
                elif system == "darwin":
                    self.console.print("  • R (macOS, optional):")
                    self.console.print("    brew install r")
                else:
                    self.console.print("  • R (optional): Install from https://www.r-project.org/")

            else:
                self.console.print(f"  • {component.title()}: Check documentation for installation instructions")

        self.console.print("\n🔧 Development Tools (Recommended):")
        self.console.print("  • VSCode Extension: Install 'rxiv-maker' extension from VS Code marketplace")
        self.console.print("    - Provides syntax highlighting, LaTeX preview, and manuscript management")
        self.console.print("  • For automatic fixing on Ubuntu/Debian: rxiv check-installation --fix")

    def _show_next_steps(self, results: dict) -> None:
        """Show next steps based on installation status."""
        all_critical_installed = all(results.get(comp, False) for comp in ["python", "pip", "latex", "pandoc"])

        if all_critical_installed:
            self.console.print("\n📋 Next steps:", style="bold blue")
            self.console.print("  1. Create a new manuscript: rxiv init MY_PAPER/")
            self.console.print("  2. Edit your manuscript files")
            self.console.print("  3. Generate your manuscript: rxiv pdf")
        else:
            self.console.print("\n📋 To get started:", style="bold blue")
            self.console.print("  1. Install missing components above")
            self.console.print("  2. Run this check again: rxiv check-installation")
            self.console.print("  3. Initialize a manuscript: rxiv init")


class VersionCommand(BaseCommand):
    """Version command implementation using the framework."""

    def execute_operation(self, detailed: bool = False, check_updates: bool = False) -> None:
        """Execute version display.

        Args:
            detailed: Show detailed version information
            check_updates: Check for available updates
        """
        from rxiv_maker import __version__

        # Check for updates if requested
        if check_updates:
            self.console.print("🔍 Checking for updates...", style="blue")
            try:
                from rxiv_maker.utils.update_checker import force_update_check

                update_available, latest_version = force_update_check()

                if update_available:
                    self.console.print(f"📦 Update available: {__version__} → {latest_version}", style="green")
                    self.console.print("   Run: pip install --upgrade rxiv-maker  (or pip3)", style="blue")
                    self.console.print("        uv tool upgrade rxiv-maker", style="blue")
                else:
                    self.console.print(f"✅ You have the latest version ({__version__})", style="green")
            except Exception as e:
                self.console.print(f"⚠️  Could not check for updates: {e}", style="yellow")

        # Show version information
        if detailed:
            self._show_detailed_version()
        else:
            self._show_basic_version()

    def _show_basic_version(self) -> None:
        """Show basic version information."""
        from rxiv_maker import __version__

        self.console.print(f"rxiv-maker version {__version__}", style="bold blue")

    def _show_detailed_version(self) -> None:
        """Show detailed version information."""
        from pathlib import Path

        from rich.table import Table

        from rxiv_maker import __version__
        from rxiv_maker.utils.platform import platform_detector

        table = Table(title="rxiv-maker Version Information", show_header=True)
        table.add_column("Component", style="cyan", width=20)
        table.add_column("Version/Value", style="green")

        # Basic version info
        table.add_row("rxiv-maker", __version__)
        table.add_row("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

        # Platform information
        try:
            platform_info = platform_detector()
            table.add_row("Platform", f"{platform_info.get('system', 'Unknown')} {platform_info.get('version', '')}")
            table.add_row("Architecture", platform_info.get("machine", "Unknown"))
        except Exception:
            table.add_row("Platform", "Detection failed")

        # Installation path
        try:
            import rxiv_maker

            install_path = str(Path(rxiv_maker.__file__).parent)
            table.add_row("Installation", install_path)
        except Exception:
            table.add_row("Installation", "Unknown")

        # Python executable
        table.add_row("Python Path", sys.executable)

        self.console.print(table)


class CompletionCommand(BaseCommand):
    """Completion command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since completion doesn't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since completion doesn't need engine."""
        pass

    def execute_operation(self, shell: str) -> None:
        """Execute shell completion installation.

        Args:
            shell: Shell type (bash, zsh, fish)
        """
        self.console.print(f"Installing {shell} completion...", style="blue")

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
                    self.console.print(f"✅ {shell} completion already installed", style="green")
                    return

            # Add completion
            with open(install_path, "a", encoding="utf-8") as f:
                f.write(f"\n# Rxiv-Maker completion\n{completion_line}\n")

            self.console.print(f"✅ {shell} completion installed to {install_path}", style="green")
            self.console.print(f"💡 Restart your shell or run: source {install_path}", style="yellow")

        except Exception as e:
            self.error_message(f"Error installing completion: {e}")
            raise CommandExecutionError(f"Completion installation failed: {e}") from e


class DeprecatedInstallDepsCommand(BaseCommand):
    """Deprecated install-deps command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since this command doesn't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since this command doesn't need engine."""
        pass

    def execute_operation(
        self,
        mode: str = "full",
        force: bool = False,
        non_interactive: bool = False,
        repair: bool = False,
        log_file: Optional[str] = None,
        ctx: Optional[click.Context] = None,
    ) -> None:
        """Execute deprecated install-deps command with redirection.

        Args:
            mode: Installation mode
            force: Force reinstallation
            non_interactive: Run in non-interactive mode
            repair: Repair broken installation
            log_file: Path to log file
            ctx: Click context
        """
        # Show deprecation warning
        self.console.print("⚠️  WARNING: 'rxiv install-deps' is deprecated!", style="bold yellow")
        self.console.print("Use 'rxiv setup --mode system-only' instead.", style="yellow")
        self.console.print("Redirecting to the new command...", style="dim")
        self.console.print()

        try:
            # Import the new setup command
            from rxiv_maker.cli.commands.setup import setup

            # Map parameters to the new setup command format
            setup_kwargs = {
                "mode": "system-only" if mode == "full" else mode,
                "reinstall": False,
                "force": force,
                "non_interactive": non_interactive,
                "check_only": False,
                "log_file": Path(log_file) if log_file else None,
            }

            if ctx is None:
                raise CommandExecutionError("Context required for setup command")

            # Call the new setup command
            setup(ctx, **setup_kwargs)

        except KeyboardInterrupt:
            self.console.print("\n⏹️  Installation interrupted by user", style="yellow")
            raise CommandExecutionError("Installation interrupted") from KeyboardInterrupt()
        except Exception as e:
            self.error_message(f"Unexpected error during installation: {e}")
            raise CommandExecutionError(f"Installation failed: {e}") from e


__all__ = [
    "CheckInstallationCommand",
    "VersionCommand",
    "CompletionCommand",
    "DeprecatedInstallDepsCommand",
]
