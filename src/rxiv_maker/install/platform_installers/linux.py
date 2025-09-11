"""Linux-specific system dependency installer."""

import os
import shutil
import subprocess
from pathlib import Path

from ..utils.logging import InstallLogger
from ..utils.progress import ProgressIndicator


class LinuxInstaller:
    """Linux-specific installer for rxiv-maker dependencies."""

    def __init__(self, logger: InstallLogger, progress: ProgressIndicator):
        """Initialize Linux installer.

        Args:
            logger: Logger instance
            progress: Progress indicator instance
        """
        self.logger = logger
        self.progress = progress

        # Detect distribution and package manager
        self.distro, self.package_manager = self._detect_distro()
        self.logger.info(f"Detected Linux distribution: {self.distro}")
        self.logger.info(f"Package manager: {self.package_manager}")

    def _detect_distro(self) -> tuple[str, str]:
        """Detect Linux distribution and package manager."""
        # Check for common distributions
        if Path("/etc/debian_version").exists():
            if self._command_exists("apt"):
                return "debian", "apt"
            elif self._command_exists("apt-get"):
                return "debian", "apt-get"

        if Path("/etc/redhat-release").exists():
            if self._command_exists("dnf"):
                return "fedora", "dnf"
            elif self._command_exists("yum"):
                return "rhel", "yum"

        if Path("/etc/arch-release").exists() and self._command_exists("pacman"):
            return "arch", "pacman"

        if Path("/etc/alpine-release").exists() and self._command_exists("apk"):
            return "alpine", "apk"

        # Fallback
        return "unknown", "unknown"

    def _command_exists(self, command: str) -> bool:
        """Check if a command exists."""
        return shutil.which(command) is not None

    def _is_root(self) -> bool:
        """Check if the current user is root."""
        try:
            return os.getuid() == 0
        except AttributeError:
            # Windows doesn't have getuid()
            return False

    def install_system_libraries(self) -> bool:
        """Install system libraries required by Python packages."""
        self.logger.info("Installing system libraries on Linux...")

        # Define packages for different package managers
        packages = {
            "apt": [
                "build-essential",
                "python3-dev",
                "libfreetype6-dev",
                "libpng-dev",
                "libjpeg-dev",
                "zlib1g-dev",
                "pkg-config",
                # Pango for text rendering
                "libpango1.0-dev",
            ],
            "apt-get": [
                "build-essential",
                "python3-dev",
                "libfreetype6-dev",
                "libpng-dev",
                "libjpeg-dev",
                "zlib1g-dev",
                "pkg-config",
                # Pango for text rendering
                "libpango1.0-dev",
            ],
            "dnf": [
                "gcc",
                "gcc-c++",
                "python3-devel",
                "freetype-devel",
                "libpng-devel",
                "libjpeg-turbo-devel",
                "zlib-devel",
                "pkgconfig",
                # Pango for text rendering
                "pango-devel",
            ],
            "yum": [
                "gcc",
                "gcc-c++",
                "python3-devel",
                "freetype-devel",
                "libpng-devel",
                "libjpeg-turbo-devel",
                "zlib-devel",
                "pkgconfig",
                # Pango for text rendering
                "pango-devel",
            ],
            "pacman": [
                "base-devel",
                "python",
                "freetype2",
                "libpng",
                "libjpeg-turbo",
                "zlib",
                "pkg-config",
                # Pango for text rendering
                "pango",
            ],
            "apk": [
                "build-base",
                "python3-dev",
                "freetype-dev",
                "libpng-dev",
                "jpeg-dev",
                "zlib-dev",
                "pkgconfig",
                # Pango for text rendering
                "pango-dev",
            ],
        }

        if self.package_manager not in packages:
            self.logger.warning(f"Unknown package manager: {self.package_manager}")
            return False

        return self._install_packages(packages[self.package_manager])

    def install_latex(self) -> bool:
        """Install LaTeX distribution on Linux."""
        self.logger.info("Installing LaTeX on Linux...")

        # Check if LaTeX is already installed
        if self._is_latex_installed():
            self.logger.success("LaTeX already installed")
            return True

        # Define LaTeX packages for different package managers
        latex_packages = {
            "apt": [
                "texlive-latex-base",
                "texlive-latex-recommended",
                "texlive-latex-extra",
                "texlive-bibtex-extra",
            ],
            "apt-get": [
                "texlive-latex-base",
                "texlive-latex-recommended",
                "texlive-latex-extra",
                "texlive-bibtex-extra",
            ],
            "dnf": [
                "texlive-latex",
                "texlive-latex-bin",
                "texlive-collection-latexrecommended",
            ],
            "yum": [
                "texlive-latex",
                "texlive-latex-bin",
                "texlive-collection-latexrecommended",
            ],
            "pacman": ["texlive-most", "texlive-bibtexextra"],
            "apk": ["texlive", "texlive-dev"],
        }

        if self.package_manager not in latex_packages:
            self.logger.warning(f"LaTeX packages not defined for {self.package_manager}")
            return False

        success = self._install_packages(latex_packages[self.package_manager])

        if success:
            self._install_latex_packages()

        return success

    def install_r(self) -> bool:
        """Install R language on Linux."""
        self.logger.info("Installing R on Linux...")

        # Check if R is already installed
        if self._is_r_installed():
            self.logger.success("R already installed")
            return True

        # Define R packages for different package managers
        r_packages = {
            "apt": ["r-base", "r-base-dev"],
            "apt-get": ["r-base", "r-base-dev"],
            "dnf": ["R", "R-devel"],
            "yum": ["R", "R-devel"],
            "pacman": ["r"],
            "apk": ["R", "R-dev"],
        }

        if self.package_manager not in r_packages:
            self.logger.warning(f"R packages not defined for {self.package_manager}")
            return False

        return self._install_packages(r_packages[self.package_manager])

    def _is_latex_installed(self) -> bool:
        """Check if LaTeX is installed."""
        try:
            result = subprocess.run(
                ["pdflatex", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
            )
            return result.returncode == 0
        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            FileNotFoundError,
            OSError,
        ):
            return False

    def _is_r_installed(self) -> bool:
        """Check if R is installed."""
        try:
            result = subprocess.run(
                ["R", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
            )
            return result.returncode == 0
        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            FileNotFoundError,
            OSError,
        ):
            return False

    def _install_packages(self, packages: list[str]) -> bool:
        """Install packages using the system package manager."""
        if not packages:
            return True

        self.logger.info(f"Installing packages: {', '.join(packages)}")

        try:
            # Check if we need sudo
            use_sudo = not self._is_root()

            # Update package lists first
            if self.package_manager in ["apt", "apt-get"]:
                self.logger.info("Updating package lists...")
                cmd = [self.package_manager, "update"]
                if use_sudo:
                    cmd = ["sudo"] + cmd
                subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=300,
                )

            # Install packages
            if self.package_manager in ["apt", "apt-get"] or self.package_manager in [
                "dnf",
                "yum",
            ]:
                cmd = [self.package_manager, "install", "-y"] + packages
            elif self.package_manager == "pacman":
                cmd = [self.package_manager, "-S", "--noconfirm"] + packages
            elif self.package_manager == "apk":
                cmd = [self.package_manager, "add"] + packages
            else:
                self.logger.error(f"Unknown package manager: {self.package_manager}")
                return False

            # Add sudo if needed
            if use_sudo:
                cmd = ["sudo"] + cmd

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=900,  # 15 minutes timeout - reduced from 30 minutes
            )

            if result.returncode == 0:
                self.logger.success("Successfully installed packages")
                return True
            else:
                self.logger.error(f"Failed to install packages: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Error installing packages: {e}")
            return False

    def _install_latex_packages(self) -> bool:
        """Install additional LaTeX packages."""
        self.logger.info("Installing additional LaTeX packages...")

        packages = [
            "latexdiff",
            "biber",
            "biblatex",
            "pgfplots",
            "adjustbox",
            "collectbox",
        ]

        # Check if we need sudo
        use_sudo = not self._is_root()

        success = True
        for package in packages:
            try:
                self.logger.debug(f"Installing LaTeX package: {package}")
                cmd = ["tlmgr", "install", package]
                if use_sudo:
                    cmd = ["sudo"] + cmd

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                if result.returncode != 0:
                    self.logger.debug(f"Failed to install {package}: {result.stderr}")
                    # Don't fail completely for optional packages
                    success = False
            except Exception as e:
                self.logger.debug(f"Error installing {package}: {e}")
                success = False

        return success
