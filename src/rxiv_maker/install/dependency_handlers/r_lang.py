"""R language dependency handler."""

import subprocess

from ..utils.logging import InstallLogger


class RLanguageHandler:
    """Handler for R language-specific operations."""

    def __init__(self, logger: InstallLogger):
        """Initialize R language handler.

        Args:
            logger: Logger instance
        """
        self.logger = logger

    def verify_installation(self) -> bool:
        """Verify R installation."""
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

    def get_version(self) -> str | None:
        """Get R version."""
        try:
            result = subprocess.run(["R", "--version"], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                lines = result.stdout.split("\n")
                for line in lines:
                    if "R version" in line:
                        return line.strip()
            return None
        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            FileNotFoundError,
            OSError,
        ):
            return None

    def install_packages(self, packages: list[str]) -> bool:
        """Install R packages."""
        if not packages:
            return True

        self.logger.info(f"Installing R packages: {', '.join(packages)}")

        # Create R command to install packages
        packages_str = "', '".join(packages)
        r_command = f"install.packages(c('{packages_str}'), repos='https://cran.rstudio.com/')"

        try:
            result = subprocess.run(
                ["R", "--vanilla", "-e", r_command],
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode == 0:
                self.logger.success("R packages installed successfully")
                return True
            else:
                self.logger.debug(f"Failed to install R packages: {result.stderr}")
                return False
        except Exception as e:
            self.logger.debug(f"Error installing R packages: {e}")
            return False

    def get_essential_packages(self) -> list[str]:
        """Get list of essential R packages."""
        return [
            "ggplot2",
            "dplyr",
            "readr",
            "tidyr",
            "scales",
            "RColorBrewer",
            "viridis",
        ]

    def verify_packages(self, packages: list[str]) -> bool:
        """Verify R packages are installed."""
        if not packages:
            return True

        packages_str = "', '".join(packages)
        r_command = f"all(c('{packages_str}') %in% installed.packages()[,'Package'])"

        try:
            result = subprocess.run(
                ["R", "--vanilla", "-e", f"cat({r_command})"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            return result.returncode == 0 and "TRUE" in result.stdout
        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            FileNotFoundError,
            OSError,
        ):
            return False
