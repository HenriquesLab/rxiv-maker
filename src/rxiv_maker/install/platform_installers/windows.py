"""Windows-specific system dependency installer."""

import subprocess
import urllib.request
from pathlib import Path

from ..utils.logging import InstallLogger
from ..utils.progress import ProgressIndicator


class WindowsInstaller:
    """Windows-specific installer for rxiv-maker dependencies."""

    def __init__(self, logger: InstallLogger, progress: ProgressIndicator):
        """Initialize Windows installer.

        Args:
            logger: Logger instance
            progress: Progress indicator instance
        """
        self.logger = logger
        self.progress = progress
        self.temp_dir = Path.home() / "AppData" / "Local" / "Temp" / "rxiv-maker"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def install_system_libraries(self) -> bool:
        """Install system libraries required by Python packages."""
        self.logger.info("Installing system libraries on Windows...")

        # On Windows, most system libraries are handled by pip wheels
        # We mainly need to ensure Visual C++ redistributables are available
        # Note: Most graphics libraries use pre-built wheels on Windows

        import importlib.util

        packages = ["matplotlib", "numpy", "PIL"]
        missing_packages = []

        for package in packages:
            if importlib.util.find_spec(package) is None:
                missing_packages.append(package)

        if not missing_packages:
            self.logger.success("System libraries already available")
            return True
        else:
            self.logger.warning(f"Some system libraries may be missing: {missing_packages}")
            # In most cases, pip will handle this during package installation
            return True

    def install_latex(self) -> bool:
        """Install LaTeX distribution on Windows."""
        self.logger.info("Installing LaTeX on Windows...")

        # Check if LaTeX is already installed
        if self._is_latex_installed():
            self.logger.success("LaTeX already installed")
            return True

        # Try different installation methods
        methods = [
            self._install_latex_winget,
            self._install_latex_chocolatey,
            self._install_latex_direct,
        ]

        for method in methods:
            try:
                if method():
                    self._install_latex_packages()
                    return True
            except Exception as e:
                self.logger.debug(f"Installation method failed: {e}")
                continue

        self.logger.error("Failed to install LaTeX using any method")
        return False

    def install_nodejs(self) -> bool:
        """Install Node.js and npm packages on Windows."""
        self.logger.info("Installing Node.js on Windows...")

        # Check if Node.js is already installed
        if self._is_nodejs_installed():
            self.logger.success("Node.js already installed")
            return self._install_npm_packages()

        # Try different installation methods
        methods = [
            self._install_nodejs_winget,
            self._install_nodejs_chocolatey,
            self._install_nodejs_direct,
        ]

        for method in methods:
            try:
                if method():
                    return self._install_npm_packages()
            except Exception as e:
                self.logger.debug(f"Node.js installation method failed: {e}")
                continue

        self.logger.error("Failed to install Node.js using any method")
        return False

    def install_r(self) -> bool:
        """Install R language on Windows."""
        self.logger.info("Installing R on Windows...")

        # Check if R is already installed
        if self._is_r_installed():
            self.logger.success("R already installed")
            return True

        # Try different installation methods
        methods = [
            self._install_r_winget,
            self._install_r_chocolatey,
            self._install_r_direct,
        ]

        for method in methods:
            try:
                if method():
                    return True
            except Exception as e:
                self.logger.debug(f"R installation method failed: {e}")
                continue

        self.logger.error("Failed to install R using any method")
        return False

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

    def _is_nodejs_installed(self) -> bool:
        """Check if Node.js is installed."""
        try:
            node_result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
            )
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

    def _install_latex_winget(self) -> bool:
        """Install LaTeX using winget."""
        self.logger.info("Trying to install LaTeX using winget...")

        try:
            # Try to install MiKTeX
            result = subprocess.run(
                ["winget", "install", "--id", "MiKTeX.MiKTeX", "--silent"],
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode == 0:
                self.logger.success("LaTeX installed using winget")
                return True
            else:
                self.logger.debug(f"winget install failed: {result.stderr}")
                return False
        except Exception as e:
            self.logger.debug(f"winget not available: {e}")
            return False

    def _install_latex_chocolatey(self) -> bool:
        """Install LaTeX using Chocolatey."""
        self.logger.info("Trying to install LaTeX using Chocolatey...")

        try:
            # Check if chocolatey is available
            subprocess.run(
                ["choco", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
            )

            # Install MiKTeX
            result = subprocess.run(
                ["choco", "install", "miktex", "-y"],
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode == 0:
                self.logger.success("LaTeX installed using Chocolatey")
                return True
            else:
                self.logger.debug(f"Chocolatey install failed: {result.stderr}")
                return False
        except Exception as e:
            self.logger.debug(f"Chocolatey not available: {e}")
            return False

    def _install_latex_direct(self) -> bool:
        """Install LaTeX using direct download."""
        self.logger.info("Trying to install LaTeX using direct download...")

        try:
            # Download MiKTeX installer
            installer_url = (
                "https://miktex.org/download/ctan/systems/win32/miktex/setup/windows-x64/basic-miktex-22.1-x64.exe"
            )
            installer_path = self.temp_dir / "miktex-installer.exe"

            self.logger.info("Downloading MiKTeX installer...")
            urllib.request.urlretrieve(installer_url, installer_path)

            # Run installer
            self.logger.info("Running MiKTeX installer...")
            result = subprocess.run(
                [str(installer_path), "--unattended"],
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode == 0:
                self.logger.success("LaTeX installed using direct download")
                return True
            else:
                self.logger.debug(f"Direct install failed: {result.stderr}")
                return False
        except Exception as e:
            self.logger.debug(f"Direct download failed: {e}")
            return False

    def _install_nodejs_winget(self) -> bool:
        """Install Node.js using winget."""
        self.logger.info("Trying to install Node.js using winget...")

        try:
            result = subprocess.run(
                ["winget", "install", "--id", "OpenJS.NodeJS", "--silent"],
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode == 0:
                self.logger.success("Node.js installed using winget")
                return True
            else:
                self.logger.debug(f"winget install failed: {result.stderr}")
                return False
        except Exception as e:
            self.logger.debug(f"winget not available: {e}")
            return False

    def _install_nodejs_chocolatey(self) -> bool:
        """Install Node.js using Chocolatey."""
        self.logger.info("Trying to install Node.js using Chocolatey...")

        try:
            # Check if chocolatey is available
            subprocess.run(
                ["choco", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
            )

            # Install Node.js
            result = subprocess.run(
                ["choco", "install", "nodejs", "-y"],
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode == 0:
                self.logger.success("Node.js installed using Chocolatey")
                return True
            else:
                self.logger.debug(f"Chocolatey install failed: {result.stderr}")
                return False
        except Exception as e:
            self.logger.debug(f"Chocolatey not available: {e}")
            return False

    def _install_nodejs_direct(self) -> bool:
        """Install Node.js using direct download."""
        self.logger.info("Trying to install Node.js using direct download...")

        try:
            # Download Node.js installer
            installer_url = "https://nodejs.org/dist/v18.17.0/node-v18.17.0-x64.msi"
            installer_path = self.temp_dir / "nodejs-installer.msi"

            self.logger.info("Downloading Node.js installer...")
            urllib.request.urlretrieve(installer_url, installer_path)

            # Run installer
            self.logger.info("Running Node.js installer...")
            result = subprocess.run(
                ["msiexec", "/i", str(installer_path), "/quiet", "/norestart"],
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode == 0:
                self.logger.success("Node.js installed using direct download")
                return True
            else:
                self.logger.debug(f"Direct install failed: {result.stderr}")
                return False
        except Exception as e:
            self.logger.debug(f"Direct download failed: {e}")
            return False

    def _install_r_winget(self) -> bool:
        """Install R using winget."""
        self.logger.info("Trying to install R using winget...")

        try:
            result = subprocess.run(
                ["winget", "install", "--id", "RProject.R", "--silent"],
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode == 0:
                self.logger.success("R installed using winget")
                return True
            else:
                self.logger.debug(f"winget install failed: {result.stderr}")
                return False
        except Exception as e:
            self.logger.debug(f"winget not available: {e}")
            return False

    def _install_r_chocolatey(self) -> bool:
        """Install R using Chocolatey."""
        self.logger.info("Trying to install R using Chocolatey...")

        try:
            # Check if chocolatey is available
            subprocess.run(
                ["choco", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
            )

            # Install R
            result = subprocess.run(
                ["choco", "install", "r.project", "-y"],
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode == 0:
                self.logger.success("R installed using Chocolatey")
                return True
            else:
                self.logger.debug(f"Chocolatey install failed: {result.stderr}")
                return False
        except Exception as e:
            self.logger.debug(f"Chocolatey not available: {e}")
            return False

    def _install_r_direct(self) -> bool:
        """Install R using direct download."""
        self.logger.info("Trying to install R using direct download...")

        try:
            # Download R installer
            installer_url = "https://cran.r-project.org/bin/windows/base/R-4.3.1-win.exe"
            installer_path = self.temp_dir / "r-installer.exe"

            self.logger.info("Downloading R installer...")
            urllib.request.urlretrieve(installer_url, installer_path)

            # Run installer
            self.logger.info("Running R installer...")
            result = subprocess.run(
                [str(installer_path), "/SILENT", "/NORESTART"],
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode == 0:
                self.logger.success("R installed using direct download")
                return True
            else:
                self.logger.debug(f"Direct install failed: {result.stderr}")
                return False
        except Exception as e:
            self.logger.debug(f"Direct download failed: {e}")
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

        success = True
        for package in packages:
            try:
                self.logger.debug(f"Installing LaTeX package: {package}")
                result = subprocess.run(
                    ["miktex", "packages", "install", package],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                if result.returncode != 0:
                    self.logger.debug(f"Failed to install {package}: {result.stderr}")
                    success = False
            except Exception as e:
                self.logger.debug(f"Error installing {package}: {e}")
                success = False

        return success

    def _install_npm_packages(self) -> bool:
        """Install required npm packages."""
        self.logger.info("No npm packages required - mermaid-cli dependency removed")

        # Mermaid diagrams are now handled via mermaid.ink API
        # No need for local mermaid-cli installation
        return True
