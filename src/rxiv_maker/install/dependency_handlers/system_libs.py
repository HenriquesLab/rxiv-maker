"""System libraries dependency handler."""

import subprocess
import sys

from ..utils.logging import InstallLogger

try:
    from packaging.version import parse as parse_version

    HAS_PACKAGING = True
except ImportError:
    HAS_PACKAGING = False


class SystemLibsHandler:
    """Handler for system libraries verification."""

    def __init__(self, logger: InstallLogger):
        """Initialize system libraries handler.

        Args:
            logger: Logger instance
        """
        self.logger = logger

    def verify_installation(self) -> bool:
        """Verify system libraries installation."""
        import importlib.util

        packages = ["matplotlib", "numpy", "pandas", "PIL", "scipy"]

        for package in packages:
            if importlib.util.find_spec(package) is None:
                self.logger.debug(f"Missing Python package: {package}")
                return False

        return True

    def get_missing_packages(self) -> list[str]:
        """Get list of missing Python packages."""
        packages_to_check = ["matplotlib", "PIL", "numpy", "pandas", "scipy", "seaborn"]

        missing = []
        for package in packages_to_check:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)

        return missing

    def verify_build_tools(self) -> bool:
        """Verify build tools are available."""
        try:
            # Check for gcc/clang
            result = subprocess.run(
                ["gcc", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
            )

            if result.returncode != 0:
                # Try clang
                result = subprocess.run(
                    ["clang", "--version"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=10,
                )

            return result.returncode == 0
        except Exception:
            return False

    def get_python_version(self) -> str:
        """Get Python version."""
        version = sys.version_info
        return f"{version.major}.{version.minor}.{version.micro}"

    def check_python_compatibility(self) -> bool:
        """Check if Python version is compatible with rxiv-maker requirements.

        Requires Python >= 3.11 as specified in pyproject.toml.
        Uses packaging library for robust version comparison if available.

        Returns:
            bool: True if Python version is compatible, False otherwise.
        """
        if HAS_PACKAGING:
            # Use packaging library for robust version comparison
            current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            required_version = "3.11.0"

            try:
                return parse_version(current_version) >= parse_version(required_version)
            except Exception as e:
                self.logger.debug(f"Error parsing version with packaging library: {e}")
                # Fall back to simple comparison
                pass

        # Fallback to simple version comparison
        version_info = sys.version_info
        return version_info.major == 3 and version_info.minor >= 11

    def get_python_version_details(self) -> dict[str, str]:
        """Get detailed Python version information for debugging.

        Returns:
            dict: Dictionary containing version details including compatibility status.
        """
        version_info = sys.version_info
        current_version = self.get_python_version()
        is_compatible = self.check_python_compatibility()

        details = {
            "version": current_version,
            "major": str(version_info.major),
            "minor": str(version_info.minor),
            "micro": str(version_info.micro),
            "is_compatible": str(is_compatible),
            "required_version": ">=3.11.0",
            "version_parser": "packaging" if HAS_PACKAGING else "builtin",
        }

        return details
