"""Core installation manager for rxiv-maker system dependencies."""

import argparse
import os
import platform
import sys
from enum import Enum
from pathlib import Path

from ...install.platform_installers import LinuxInstaller, MacOSInstaller, WindowsInstaller
from ...install.utils.logging import InstallLogger
from ...install.utils.progress import ProgressIndicator
from ...install.utils.verification import verify_installation


class InstallMode(Enum):
    """Installation mode options."""

    FULL = "full"  # Install all dependencies
    MINIMAL = "minimal"  # Python packages + essential LaTeX
    CORE = "core"  # Python packages + LaTeX (skip Node.js, R)
    SKIP_SYSTEM = "skip-system"  # Python packages only


class InstallManager:
    """Manages system dependency installation across platforms."""

    def __init__(
        self,
        mode: InstallMode = InstallMode.FULL,
        verbose: bool = False,
        force: bool = False,
        interactive: bool = True,
        log_file: Path | None = None,
    ):
        """Initialize the installation manager.

        Args:
            mode: Installation mode (full, minimal, core, skip-system)
            verbose: Enable verbose logging
            force: Force reinstallation of existing dependencies
            interactive: Allow interactive prompts
            log_file: Path to log file (auto-generated if None)
        """
        self.mode = mode
        self.verbose = verbose
        self.force = force
        self.interactive = interactive

        # Initialize logging
        self.logger = InstallLogger(log_file=log_file, verbose=verbose)

        # Initialize progress indicator
        self.progress = ProgressIndicator(verbose=verbose)

        # Platform detection
        self.platform_name = platform.system()
        self.platform_installer = self._get_platform_installer()

        # Track installation state
        self.installation_results: dict[str, bool] = {}
        self.errors: list[str] = []

    def _get_platform_installer(self):
        """Get the appropriate platform installer."""
        if self.platform_name == "Windows":
            return WindowsInstaller(self.logger, self.progress)
        elif self.platform_name == "Darwin":
            return MacOSInstaller(self.logger, self.progress)
        elif self.platform_name == "Linux":
            return LinuxInstaller(self.logger, self.progress)
        else:
            raise RuntimeError(f"Unsupported platform: {self.platform_name}")

    def install(self) -> bool:
        """Run the complete installation process.

        Returns:
            True if installation succeeded, False otherwise
        """
        self.logger.info(f"Starting rxiv-maker installation in {self.mode.value} mode")
        self.logger.info(f"Platform: {self.platform_name}")

        try:
            # Check if running in special environments
            if self._is_in_docker():
                self.logger.info("Docker container detected - skipping system dependencies")
                return True

            if self._is_in_conda():
                self.logger.info("Conda environment detected - using conda-aware installation")
                return self._run_conda_installation()

            # Pre-installation checks
            if not self._pre_install_checks():
                return False

            # Run platform-specific installation
            success = self._run_platform_installation()

            # Post-installation verification
            if success:
                success = self._post_install_verification()

            # Generate installation report
            self._generate_report()

            return success

        except Exception as e:
            self.logger.error(f"Installation failed: {str(e)}")
            self.errors.append(str(e))
            return False

    def _is_in_docker(self) -> bool:
        """Check if running in a Docker container."""
        return (
            os.path.exists("/.dockerenv")
            or os.path.exists("/proc/1/cgroup")
            and "docker" in open("/proc/1/cgroup", encoding="utf-8").read()
        )

    def _is_in_conda(self) -> bool:
        """Check if running in a conda/mamba environment."""
        return (
            os.getenv("CONDA_DEFAULT_ENV") is not None
            or os.getenv("CONDA_PREFIX") is not None
            or os.getenv("MAMBA_DEFAULT_ENV") is not None
            or os.getenv("MAMBA_PREFIX") is not None
        )

    def _get_conda_executable(self) -> str | None:
        """Get the conda or mamba executable to use."""
        # Import here to avoid circular dependency
        import shutil

        # Prefer mamba if available (faster)
        if shutil.which("mamba"):
            return "mamba"
        elif shutil.which("conda"):
            return "conda"
        return None

    def _run_conda_installation(self) -> bool:
        """Run conda-specific installation process."""
        conda_exe = self._get_conda_executable()
        if not conda_exe:
            self.logger.error("Conda/mamba executable not found despite being in conda environment")
            return False

        env_name = os.getenv("CONDA_DEFAULT_ENV") or os.getenv("MAMBA_DEFAULT_ENV", "unknown")
        self.logger.info(f"Installing dependencies using {conda_exe} in environment: {env_name}")

        success = True

        # Install Python packages that are better from conda-forge
        conda_packages = []

        # Define what to install based on mode
        install_latex = self.mode in [
            InstallMode.FULL,
            InstallMode.MINIMAL,
            InstallMode.CORE,
        ]
        install_nodejs = self.mode in [InstallMode.FULL, InstallMode.CORE]
        install_r = self.mode == InstallMode.FULL

        # Add packages available in conda-forge
        if install_r:
            conda_packages.append("r-base")
        if install_nodejs:
            conda_packages.append("nodejs")

        # Install conda packages if any
        if conda_packages:
            self.progress.start_task(f"Installing packages with {conda_exe}")
            try:
                import subprocess

                result = subprocess.run(
                    [conda_exe, "install", "-y", "-c", "conda-forge"] + conda_packages,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if result.returncode == 0:
                    self.logger.info(f"Successfully installed conda packages: {', '.join(conda_packages)}")
                    for pkg in conda_packages:
                        self.installation_results[pkg] = True
                else:
                    self.logger.warning(f"Conda installation failed: {result.stderr}")
                    success = False
                    for pkg in conda_packages:
                        self.installation_results[pkg] = False
            except Exception as e:
                self.logger.error(f"Error running conda install: {e}")
                success = False
            self.progress.complete_task()

        # For LaTeX, still use system package manager as conda's latex is limited
        if install_latex:
            self.progress.start_task("Installing LaTeX distribution (system package manager)")
            result = self.platform_installer.install_latex()
            self.installation_results["latex"] = result
            if not result:
                success = False
                self.errors.append("Failed to install LaTeX")
            self.progress.complete_task()

        # Post-installation verification
        if success:
            success = self._post_install_verification()

        # Generate installation report
        self._generate_report()

        return success

    def _pre_install_checks(self) -> bool:
        """Run pre-installation checks."""
        self.logger.info("Running pre-installation checks...")

        # Check for admin privileges if needed
        if self.platform_name == "Windows" and not self._has_admin_privileges():
            self.logger.warning("Administrator privileges may be required for system installations")

        # Check available disk space
        if not self._check_disk_space():
            self.logger.error("Insufficient disk space for installation")
            return False

        # Check internet connectivity
        if not self._check_internet():
            self.logger.warning("No internet connection - some installations may fail")

        return True

    def _has_admin_privileges(self) -> bool:
        """Check if running with administrator privileges."""
        try:
            import ctypes

            if hasattr(ctypes, "windll"):
                return ctypes.windll.shell32.IsUserAnAdmin()  # type: ignore[attr-defined]
            return False
        except (ImportError, OSError, Exception):
            return False

    def _check_disk_space(self, required_gb: float = 2.0) -> bool:
        """Check available disk space."""
        try:
            import shutil

            free_bytes = shutil.disk_usage(".").free
            free_gb = free_bytes / (1024**3)
            return free_gb >= required_gb
        except (ImportError, OSError, Exception):
            return True  # Assume sufficient space if check fails

    def _check_internet(self) -> bool:
        """Check internet connectivity."""
        try:
            import urllib.request

            urllib.request.urlopen("https://www.google.com", timeout=5)
            return True
        except (ImportError, OSError, Exception):
            return False

    def _run_platform_installation(self) -> bool:
        """Run platform-specific installation."""
        self.logger.info(f"Running {self.platform_name} installation...")

        # Define what to install based on mode
        install_latex = self.mode in [
            InstallMode.FULL,
            InstallMode.MINIMAL,
            InstallMode.CORE,
        ]
        install_nodejs = self.mode in [InstallMode.FULL, InstallMode.CORE]
        install_r = self.mode == InstallMode.FULL
        install_system_libs = self.mode in [
            InstallMode.FULL,
            InstallMode.MINIMAL,
            InstallMode.CORE,
        ]

        success = True

        # Install system libraries first
        if install_system_libs:
            self.progress.start_task("Installing system libraries")
            result = self.platform_installer.install_system_libraries()
            self.installation_results["system_libs"] = result
            if not result:
                success = False
                self.errors.append("Failed to install system libraries")
            self.progress.complete_task()

        # Install LaTeX
        if install_latex:
            self.progress.start_task("Installing LaTeX distribution")
            result = self.platform_installer.install_latex()
            self.installation_results["latex"] = result
            if not result:
                success = False
                self.errors.append("Failed to install LaTeX")
            self.progress.complete_task()

        # Install Node.js
        if install_nodejs:
            self.progress.start_task("Installing Node.js and npm packages")
            result = self.platform_installer.install_nodejs()
            self.installation_results["nodejs"] = result
            if not result:
                success = False
                self.errors.append("Failed to install Node.js")
            self.progress.complete_task()

        # Install R
        if install_r:
            self.progress.start_task("Installing R language")
            result = self.platform_installer.install_r()
            self.installation_results["r"] = result
            if not result:
                success = False
                self.errors.append("Failed to install R")
            self.progress.complete_task()

        return success

    def _post_install_verification(self) -> bool:
        """Run post-installation verification."""
        self.logger.info("Verifying installation...")

        verification_results = verify_installation(verbose=self.verbose)

        # Log verification results
        for component, result in verification_results.items():
            if result:
                self.logger.info(f"✓ {component} verification passed")
            else:
                self.logger.warning(f"✗ {component} verification failed")

        # Return True if critical components are working
        critical_components = ["python", "latex"]
        return all(verification_results.get(comp, False) for comp in critical_components)

    def _generate_report(self):
        """Generate installation report."""
        self.logger.info("=" * 60)
        self.logger.info("INSTALLATION REPORT")
        self.logger.info("=" * 60)

        # Installation results
        self.logger.info("Installation Results:")
        for component, result in self.installation_results.items():
            status = "✓ SUCCESS" if result else "✗ FAILED"
            self.logger.info(f"  {component}: {status}")

        # Errors
        if self.errors:
            self.logger.info("Errors encountered:")
            for error in self.errors:
                self.logger.info(f"  - {error}")

        # Next steps
        self.logger.info("Next steps:")
        self.logger.info("  1. Run 'rxiv --check-installation' to verify setup")
        self.logger.info("  2. Try 'rxiv init my-paper' to create a test manuscript")
        self.logger.info("  3. Check the documentation at https://github.com/henriqueslab/rxiv-maker")

        self.logger.info("=" * 60)

    def repair(self) -> bool:
        """Repair broken installation."""
        self.logger.info("Starting installation repair...")

        # Force reinstallation of failed components
        self.force = True

        # Check what's broken
        verification_results = verify_installation(verbose=self.verbose)
        broken_components = [comp for comp, result in verification_results.items() if not result]

        if not broken_components:
            self.logger.info("No broken components found")
            return True

        self.logger.info(f"Repairing components: {', '.join(broken_components)}")

        # Repair each broken component
        success = True
        for component in broken_components:
            if component == "latex":
                result = self.platform_installer.install_latex()
            elif component == "nodejs":
                result = self.platform_installer.install_nodejs()
            elif component == "r":
                result = self.platform_installer.install_r()
            else:
                continue

            if not result:
                success = False
                self.errors.append(f"Failed to repair {component}")

        return success


def main():
    """Main entry point for the installation manager."""
    parser = argparse.ArgumentParser(description="Install rxiv-maker system dependencies")
    parser.add_argument(
        "--mode",
        choices=[mode.value for mode in InstallMode],
        default=InstallMode.FULL.value,
        help="Installation mode (default: full)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force reinstallation of existing dependencies",
    )
    parser.add_argument("--non-interactive", action="store_true", help="Run in non-interactive mode")
    parser.add_argument("--repair", action="store_true", help="Repair broken installation")
    parser.add_argument("--log-file", type=Path, help="Path to log file")

    args = parser.parse_args()

    # Create installation manager
    manager = InstallManager(
        mode=InstallMode(args.mode),
        verbose=args.verbose,
        force=args.force,
        interactive=not args.non_interactive,
        log_file=args.log_file,
    )

    # Run installation or repair
    success = manager.repair() if args.repair else manager.install()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
