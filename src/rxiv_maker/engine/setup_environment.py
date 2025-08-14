"""Environment setup command for Rxiv-Maker.

This script handles cross-platform environment setup including:
- uv installation
- Virtual environment management
- Dependency installation
- Environment validation
- System dependency checking
"""

import os
import subprocess
import sys
from pathlib import Path

# Add the parent directory to the path to allow imports when run as a script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rxiv_maker.utils.dependency_checker import DependencyChecker
from rxiv_maker.utils.platform import platform_detector


class EnvironmentSetup:
    """Handle environment setup operations."""

    def __init__(
        self,
        reinstall: bool = False,
        verbose: bool = False,
        check_system_deps: bool = True,
    ):
        """Initialize environment setup.

        Args:
            reinstall: Whether to reinstall (remove existing .venv)
            verbose: Whether to show verbose output
            check_system_deps: Whether to check system dependencies
        """
        self.reinstall = reinstall
        self.verbose = verbose
        self.check_system_deps = check_system_deps
        self.platform = platform_detector
        self.dependency_checker = DependencyChecker(verbose=verbose)

    def log(self, message: str, level: str = "INFO"):
        """Log a message with appropriate formatting."""
        if level == "INFO":
            print(f"✅ {message}")
        elif level == "WARNING":
            print(f"⚠️  {message}")
        elif level == "ERROR":
            print(f"❌ {message}")
        elif level == "STEP":
            print(f"🔧 {message}")
        else:
            print(message)

    def check_uv_installation(self) -> bool:
        """Check if uv is installed and working."""
        try:
            result = subprocess.run(["uv", "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip()
                if self.verbose:
                    self.log(f"Found uv: {version}")
                return True
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def install_uv(self) -> bool:
        """Install uv package manager using secure subprocess calls."""
        self.log("Installing uv package manager...", "STEP")

        try:
            if self.platform.is_windows():
                # Use PowerShell on Windows with secure list arguments
                result = subprocess.run(
                    ["powershell", "-Command", "irm https://astral.sh/uv/install.ps1 | iex"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=300,  # 5 minute timeout for installation
                )
            else:
                # Use secure approach for Unix-like systems
                # First, download the installation script
                curl_result = subprocess.run(
                    ["curl", "-LsSf", "https://astral.sh/uv/install.sh"],
                    capture_output=True,
                    text=True,
                    timeout=60,  # 1 minute timeout for download
                )

                if curl_result.returncode != 0:
                    self.log(f"Failed to download uv installer: {curl_result.stderr}", "ERROR")
                    return False

                # Execute the downloaded script securely
                result = subprocess.run(
                    ["sh", "-c", curl_result.stdout],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=240,  # 4 minute timeout for installation
                )
            if result.returncode == 0:
                self.log("uv installed successfully")
                return True
            else:
                self.log(f"Failed to install uv: {result.stderr}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Error installing uv: {e}", "ERROR")
            return False

    def remove_existing_venv(self) -> bool:
        """Remove existing virtual environment."""
        venv_path = Path(".venv")
        if venv_path.exists():
            self.log("Removing existing virtual environment...", "STEP")
            success = self.platform.remove_directory(venv_path)
            if success:
                self.log("Existing virtual environment removed")
                return True
            else:
                self.log("Failed to remove existing virtual environment", "ERROR")
                return False
        return True

    def sync_dependencies(self) -> bool:
        """Sync dependencies using uv."""
        self.log("Installing dependencies with uv...", "STEP")

        try:
            # Run uv sync with development dependencies
            result = subprocess.run(
                ["uv", "sync", "--dev"],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
            )

            if result.returncode == 0:
                self.log("Dependencies installed successfully")
                if self.verbose and result.stdout:
                    print(result.stdout)
                return True
            else:
                self.log(f"Failed to install dependencies: {result.stderr}", "ERROR")
                return False
        except subprocess.TimeoutExpired:
            self.log("Dependency installation timed out", "ERROR")
            return False
        except Exception as e:
            self.log(f"Error installing dependencies: {e}", "ERROR")
            return False

    def check_system_dependencies(self) -> bool:
        """Check system dependencies and provide guidance."""
        if not self.check_system_deps:
            return True

        self.log("Checking system dependencies...", "STEP")

        # Check all dependencies
        self.dependency_checker.check_all_dependencies()

        # Get missing required dependencies
        missing_required = self.dependency_checker.get_missing_required_dependencies()
        missing_optional = self.dependency_checker.get_missing_optional_dependencies()

        if missing_required:
            self.log("Missing required system dependencies detected", "WARNING")
            print()
            self.dependency_checker.print_dependency_report()
            print()
            self.log(
                "Please install missing required dependencies before continuing",
                "ERROR",
            )
            return False
        else:
            self.log("All required system dependencies found")

            if missing_optional and self.verbose:
                print()
                self.log("Some optional dependencies are missing:", "WARNING")
                for dep in missing_optional:
                    print(f"  • {dep.name} - {dep.description}")
                print("  Use 'make check-deps' for detailed installation instructions")
                print()

        return True

    def validate_environment(self) -> bool:
        """Validate the environment setup."""
        self.log("Validating environment setup...", "STEP")

        # Check if virtual environment was created
        venv_python = self.platform.get_venv_python_path()
        if not venv_python or not Path(venv_python).exists():
            self.log("Virtual environment not found", "ERROR")
            return False

        # Try to run python in the virtual environment
        try:
            result = subprocess.run([venv_python, "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                python_version = result.stdout.strip()
                self.log(f"Python environment validated: {python_version}")
                return True
            else:
                self.log("Failed to validate Python environment", "ERROR")
                return False
        except Exception as e:
            self.log(f"Error validating environment: {e}", "ERROR")
            return False

    def show_completion_message(self):
        """Show completion message with next steps."""
        self.log("Setup complete! Here's what you can do next:")
        print("  📄 Run 'rxiv pdf' to create your first document")
        print("  🔍 Run 'rxiv validate' to check your manuscript")
        print("  🎨 Add figure scripts to MANUSCRIPT/FIGURES/ directory")
        print("  📚 Run 'rxiv --help' to see all available commands")
        print("  🔧 Run 'rxiv check-deps' to verify system dependencies")
        print()

        # Check if we have missing dependencies to show appropriate guidance
        if self.check_system_deps and hasattr(self, "dependency_checker"):
            missing_required = self.dependency_checker.get_missing_required_dependencies()
            missing_optional = self.dependency_checker.get_missing_optional_dependencies()

            if missing_required:
                print("⚠️  Some required dependencies are missing. Check them with:")
                print("   make check-deps")
            elif missing_optional:
                print("💡 Some optional dependencies are missing. For full functionality:")
                print("   make check-deps")
            else:
                print("✅ All system dependencies are available!")
        else:
            print("💡 Note: System dependencies (LaTeX, Node.js, R) may be required")
            print("   Run 'make check-deps' to verify your system is ready")

        print()
        print(f"🌐 Platform: {self.platform.platform}")
        print(f"🐍 Python: {self.platform.python_cmd}")

        venv_path = self.platform.get_venv_python_path()
        if venv_path:
            print(f"🔧 Virtual environment: {venv_path}")

        print("🎉 Rxiv-Maker Python environment setup complete!")

    def run_setup(self) -> bool:
        """Run the complete setup process."""
        self.log(
            f"Setting up Python environment with uv on {self.platform.platform}...",
            "STEP",
        )

        # Step 1: Check system dependencies first (if enabled)
        if self.check_system_deps:
            if not self.check_system_dependencies():
                print()
                self.log("System dependency check failed. You can:", "WARNING")
                print("  • Install missing dependencies and run 'make setup' again")
                print(
                    "  • Skip dependency checking with 'python src/rxiv_maker/commands/setup_environment.py --no-check-system-deps'"
                )
                print("  • Use Docker mode instead: 'make pdf RXIV_ENGINE=DOCKER'")
                return False

        # Step 2: Remove existing environment if reinstalling
        if self.reinstall and not self.remove_existing_venv():
            return False

        # Step 3: Check/install uv
        if not self.check_uv_installation():
            if not self.install_uv():
                return False

            # Verify installation
            if not self.check_uv_installation():
                self.log("uv installation verification failed", "ERROR")
                return False
        else:
            self.log("Found uv, using it for environment management")

        # Step 4: Sync dependencies
        if not self.sync_dependencies():
            return False

        # Step 5: Validate environment
        if not self.validate_environment():
            return False

        # Step 6: Show completion message
        self.show_completion_message()

        return True


def main():
    """Main entry point for setup environment command."""
    import argparse

    parser = argparse.ArgumentParser(description="Set up development environment for rxiv-maker")
    parser.add_argument(
        "--reinstall",
        action="store_true",
        help="Reinstall dependencies (removes .venv and creates new one)",
    )
    parser.add_argument("--check-deps-only", action="store_true", help="Only check system dependencies")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Initialize setup manager
    setup_manager = EnvironmentSetup(
        reinstall=args.reinstall,
        check_system_deps=not args.check_deps_only,
        verbose=args.verbose,
    )

    # Run setup
    success = setup_manager.run_setup()

    if not success:
        exit(1)


if __name__ == "__main__":
    main()
