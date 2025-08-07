"""System dependency checker for Rxiv-Maker.

This module provides comprehensive checking of system dependencies required
for Rxiv-Maker functionality, including LaTeX, Make, Node.js, and R.
"""

import shutil
import subprocess
from dataclasses import dataclass

# Handle imports when run as script or module
try:
    from .platform import platform_detector
except ImportError:
    # Fallback for standalone execution
    from .platform import platform_detector


@dataclass
class DependencyInfo:
    """Information about a system dependency."""

    name: str
    required: bool
    found: bool
    version: str | None = None
    path: str | None = None
    install_commands: dict[str, str] | None = None
    description: str = ""
    alternative: str | None = None


class DependencyChecker:
    """Check system dependencies for Rxiv-Maker."""

    def __init__(self, verbose: bool = False):
        """Initialize dependency checker.

        Args:
            verbose: Whether to show verbose output
        """
        self.verbose = verbose
        self.platform = platform_detector
        self.dependencies: list[DependencyInfo] = []

    def log(self, message: str, level: str = "INFO"):
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            if level == "INFO":
                print(f"ℹ️  {message}")
            elif level == "WARNING":
                print(f"⚠️  {message}")
            elif level == "ERROR":
                print(f"❌ {message}")
            elif level == "SUCCESS":
                print(f"✅ {message}")
            else:
                print(message)

    def check_command_version(
        self, command: str, version_flag: str = "--version"
    ) -> tuple[bool, str | None, str | None]:
        """Check if a command exists and get its version.

        Args:
            command: Command to check
            version_flag: Flag to get version (default: --version)

        Returns:
            Tuple of (found, version, path)
        """
        try:
            # Check if command exists
            cmd_path = shutil.which(command)
            if not cmd_path:
                return False, None, None

            # Get version
            result = subprocess.run([command, version_flag], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                version = result.stdout.strip().split("\n")[0]
                return True, version, cmd_path
            else:
                return True, None, cmd_path

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False, None, None

    def check_latex(self) -> DependencyInfo:
        """Check for LaTeX installation."""
        self.log("Checking LaTeX installation...")

        # Check for pdflatex first (most common)
        found, version, path = self.check_command_version("pdflatex")

        if not found:
            # Try xelatex as alternative
            found, version, path = self.check_command_version("xelatex")

        # Platform-specific installation commands
        install_commands = {
            "Windows": "choco install -y miktex",
            "macOS": "brew install --cask mactex-no-gui",
            "Linux": "sudo apt install -y texlive-latex-recommended texlive-fonts-recommended",
        }

        description = "LaTeX distribution for PDF compilation"
        alternative = "Use Docker mode: make pdf RXIV_ENGINE=DOCKER"

        return DependencyInfo(
            name="LaTeX",
            required=True,
            found=found,
            version=version,
            path=path,
            install_commands=install_commands,
            description=description,
            alternative=alternative,
        )

    def check_make(self) -> DependencyInfo:
        """Check for Make build tool."""
        self.log("Checking Make build tool...")

        found, version, path = self.check_command_version("make")

        # Platform-specific installation commands
        install_commands = {
            "Windows": "choco install -y make (or scoop install make)",
            "macOS": "xcode-select --install",
            "Linux": "sudo apt install -y make",
        }

        description = "Build automation tool (required for Makefile commands)"

        return DependencyInfo(
            name="Make",
            required=True,
            found=found,
            version=version,
            path=path,
            install_commands=install_commands,
            description=description,
        )

    def check_r(self) -> DependencyInfo:
        """Check for R (optional, for R figure scripts)."""
        self.log("Checking R...")

        found, version, path = self.check_command_version("R", "--version")

        # Platform-specific installation commands
        install_commands = {
            "Windows": "choco install -y r.project",
            "macOS": "brew install r",
            "Linux": "sudo apt install -y r-base r-base-dev",
        }

        description = "R statistical software (optional, for R figure scripts)"
        alternative = "Use Python for figures or Docker mode"

        return DependencyInfo(
            name="R",
            required=False,  # Optional
            found=found,
            version=version,
            path=path,
            install_commands=install_commands,
            description=description,
            alternative=alternative,
        )

    def check_python(self) -> DependencyInfo:
        """Check for Python (should already be available)."""
        self.log("Checking Python...")

        # Use the platform's detected Python command
        python_cmd = self.platform.python_cmd.split()[0]  # Remove 'uv run' if present

        found, version, path = self.check_command_version(python_cmd)

        description = "Python interpreter (required for Rxiv-Maker)"

        return DependencyInfo(
            name="Python",
            required=True,
            found=found,
            version=version,
            path=path,
            description=description,
        )

    def check_git(self) -> DependencyInfo:
        """Check for Git (recommended for version control)."""
        self.log("Checking Git...")

        found, version, path = self.check_command_version("git")

        # Platform-specific installation commands
        install_commands = {
            "Windows": "choco install -y git",
            "macOS": "xcode-select --install (or brew install git)",
            "Linux": "sudo apt install -y git",
        }

        description = "Version control system (recommended)"

        return DependencyInfo(
            name="Git",
            required=False,
            found=found,
            version=version,
            path=path,
            install_commands=install_commands,
            description=description,
        )

    def check_conda(self) -> DependencyInfo:
        """Check for conda/mamba package manager (optional)."""
        self.log("Checking conda/mamba...")

        # Check for mamba first (faster), then conda
        conda_exe = self.platform.get_conda_executable()
        found = conda_exe is not None
        version = None
        path = None

        if found:
            found, version, path = self.check_command_version(conda_exe)

        # Installation commands for conda
        install_commands = {
            "Windows": "Download Miniconda from https://docs.conda.io/en/latest/miniconda.html",
            "macOS": "brew install miniconda (or download from conda.io)",
            "Linux": "wget -O miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && bash miniconda.sh",
        }

        # Check if running in conda environment
        env_info = ""
        if self.platform.is_in_conda_env():
            env_name = self.platform.get_conda_env_name() or "base"
            env_info = f" (current environment: {env_name})"

        description = f"Conda/Mamba package manager{env_info}"
        alternative = "Use pip for package installation or Docker mode"

        return DependencyInfo(
            name="Conda/Mamba",
            required=False,
            found=found,
            version=version,
            path=path,
            install_commands=install_commands,
            description=description,
            alternative=alternative,
        )

    def check_all_dependencies(self) -> list[DependencyInfo]:
        """Check all system dependencies.

        Returns:
            List of dependency information
        """
        self.log(f"Checking system dependencies on {self.platform.platform}...")

        self.dependencies = [
            self.check_python(),
            self.check_make(),
            self.check_latex(),
            self.check_r(),
            self.check_git(),
            self.check_conda(),
        ]

        return self.dependencies

    def get_missing_required_dependencies(self) -> list[DependencyInfo]:
        """Get list of missing required dependencies."""
        return [dep for dep in self.dependencies if dep.required and not dep.found]

    def get_missing_optional_dependencies(self) -> list[DependencyInfo]:
        """Get list of missing optional dependencies."""
        return [dep for dep in self.dependencies if not dep.required and not dep.found]

    def has_all_required_dependencies(self) -> bool:
        """Check if all required dependencies are available."""
        return len(self.get_missing_required_dependencies()) == 0

    def print_dependency_report(self):
        """Print a comprehensive dependency report."""
        print(f"\n🔍 System Dependency Report - {self.platform.platform}")
        print("=" * 60)

        # Required dependencies
        print("\n📋 Required Dependencies:")
        required_deps = [dep for dep in self.dependencies if dep.required]
        for dep in required_deps:
            status = "✅" if dep.found else "❌"
            version_info = f" ({dep.version})" if dep.version else ""
            print(f"  {status} {dep.name}{version_info}")
            if not dep.found:
                print(f"     Description: {dep.description}")

        # Optional dependencies
        print("\n🔧 Optional Dependencies:")
        optional_deps = [dep for dep in self.dependencies if not dep.required]
        for dep in optional_deps:
            status = "✅" if dep.found else "⚪"
            version_info = f" ({dep.version})" if dep.version else ""
            print(f"  {status} {dep.name}{version_info}")

        # Missing dependencies with installation instructions
        missing_required = self.get_missing_required_dependencies()
        missing_optional = self.get_missing_optional_dependencies()

        if missing_required:
            print(f"\n❌ Missing Required Dependencies ({len(missing_required)}):")
            self._print_installation_instructions(missing_required)

        if missing_optional:
            print(f"\n⚪ Missing Optional Dependencies ({len(missing_optional)}):")
            self._print_installation_instructions(missing_optional)

        # Summary and recommendations
        self._print_summary_and_recommendations()

    def _print_installation_instructions(self, dependencies: list[DependencyInfo]):
        """Print installation instructions for missing dependencies."""
        platform_name = self.platform.platform

        for dep in dependencies:
            print(f"\n  📦 {dep.name}")
            print(f"     Description: {dep.description}")

            if dep.install_commands and platform_name in dep.install_commands:
                print(f"     Install: {dep.install_commands[platform_name]}")

            if dep.alternative:
                print(f"     Alternative: {dep.alternative}")

    def _print_summary_and_recommendations(self):
        """Print summary and recommendations."""
        missing_required = self.get_missing_required_dependencies()
        missing_optional = self.get_missing_optional_dependencies()

        print("\n📊 Summary:")
        print(f"  • Platform: {self.platform.platform}")
        print(
            f"  • Required dependencies: {len([d for d in self.dependencies if d.required and d.found])}/{len([d for d in self.dependencies if d.required])}"
        )
        print(
            f"  • Optional dependencies: {len([d for d in self.dependencies if not d.required and d.found])}/{len([d for d in self.dependencies if not d.required])}"
        )

        if missing_required:
            print(f"\n⚠️  You have {len(missing_required)} missing required dependencies.")
            print("   Please install them before running 'make pdf'.")
        else:
            print("\n✅ All required dependencies are available!")
            print("   You can run 'make pdf' to generate PDFs.")

        if missing_optional:
            print(f"\n💡 Optional: Install {len(missing_optional)} additional dependencies for full functionality.")

        # Docker recommendation
        if missing_required or len(missing_optional) > 1:
            print("\n🐳 Alternative: Use Docker mode to avoid local dependency installation:")
            print("   make pdf RXIV_ENGINE=DOCKER")
            print("   (Only requires Docker and Make to be installed)")


def check_system_dependencies(verbose: bool = False) -> DependencyChecker:
    """Check all system dependencies and return checker instance.

    Args:
        verbose: Whether to show verbose output

    Returns:
        DependencyChecker instance with results
    """
    checker = DependencyChecker(verbose=verbose)
    checker.check_all_dependencies()
    return checker


def print_dependency_report(verbose: bool = False):
    """Check and print a comprehensive dependency report.

    Args:
        verbose: Whether to show verbose output during checks
    """
    checker = check_system_dependencies(verbose=verbose)
    checker.print_dependency_report()


if __name__ == "__main__":
    # Command-line interface
    import argparse

    parser = argparse.ArgumentParser(description="Check Rxiv-Maker system dependencies")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output during checks")

    args = parser.parse_args()

    print_dependency_report(verbose=args.verbose)
