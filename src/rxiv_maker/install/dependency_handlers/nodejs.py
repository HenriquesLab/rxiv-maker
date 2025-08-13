"""Node.js dependency handler."""

import subprocess

from ..utils.logging import InstallLogger


class NodeJSHandler:
    """Handler for Node.js-specific operations."""

    def __init__(self, logger: InstallLogger):
        """Initialize Node.js handler.

        Args:
            logger: Logger instance
        """
        self.logger = logger

    def verify_installation(self) -> bool:
        """Verify Node.js installation."""
        try:
            # Check node
            node_result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
            )

            # Check npm
            npm_result = subprocess.run(
                ["npm", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
            )

            return node_result.returncode == 0 and npm_result.returncode == 0
        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            FileNotFoundError,
            OSError,
        ):
            return False

    def get_version(self) -> str | None:
        """Get Node.js version."""
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            FileNotFoundError,
            OSError,
        ):
            return None

    def get_npm_version(self) -> str | None:
        """Get npm version."""
        try:
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            FileNotFoundError,
            OSError,
        ):
            return None

    def install_packages(self, packages: list[str], global_install: bool = True) -> bool:
        """Install npm packages."""
        if not packages:
            return True

        self.logger.info(f"Installing npm packages: {', '.join(packages)}")

        success = True
        for package in packages:
            try:
                cmd = ["npm", "install"]
                if global_install:
                    cmd.append("-g")
                cmd.append(package)

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

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
        """Get list of essential npm packages."""
        return []

    def verify_mermaid(self) -> bool:
        """Verify Mermaid CLI installation.

        Note: Mermaid CLI dependency removed in favor of Python-based solutions.
        This always returns False to indicate mermaid CLI is not required.
        """
        return False  # No longer using mermaid CLI (puppeteer dependency removed)
