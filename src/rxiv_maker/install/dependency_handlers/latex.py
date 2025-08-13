"""LaTeX dependency handler."""

import subprocess

from ..utils.logging import InstallLogger


class LaTeXHandler:
    """Handler for LaTeX-specific operations."""

    def __init__(self, logger: InstallLogger):
        """Initialize LaTeX handler.

        Args:
            logger: Logger instance
        """
        self.logger = logger

    def verify_installation(self) -> bool:
        """Verify LaTeX installation."""
        try:
            # Check pdflatex
            result = subprocess.run(
                ["pdflatex", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
            )

            if result.returncode != 0:
                return False

            # Check bibtex
            result = subprocess.run(
                ["bibtex", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
            )

            return result.returncode == 0
        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            FileNotFoundError,
        ):
            return False

    def get_version(self) -> str | None:
        """Get LaTeX version."""
        try:
            result = subprocess.run(["pdflatex", "--version"], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                lines = result.stdout.split("\n")
                for line in lines:
                    if "pdfTeX" in line:
                        return line.strip()
            return None
        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            FileNotFoundError,
        ):
            return None

    def install_packages(self, packages: list[str]) -> bool:
        """Install LaTeX packages using tlmgr."""
        if not packages:
            return True

        self.logger.info(f"Installing LaTeX packages: {', '.join(packages)}")

        success = True
        for package in packages:
            try:
                result = subprocess.run(
                    ["tlmgr", "install", package],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                if result.returncode != 0:
                    self.logger.debug(f"Failed to install {package}: {result.stderr}")
                    success = False
                else:
                    self.logger.debug(f"Successfully installed {package}")
            except Exception as e:
                self.logger.debug(f"Error installing {package}: {e}")
                success = False

        return success

    def get_essential_packages(self) -> list[str]:
        """Get list of essential LaTeX packages."""
        return [
            "latexdiff",
            "biber",
            "biblatex",
            "pgfplots",
            "adjustbox",
            "collectbox",
            "xcolor",
            "graphicx",
            "hyperref",
            "amsmath",
            "amsfonts",
            "amssymb",
        ]
