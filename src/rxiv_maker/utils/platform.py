"""Platform detection and compatibility utilities for Rxiv-Maker.

This module provides cross-platform utilities for detecting the operating system
and handling platform-specific operations like path management and command execution.
"""

import logging
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


class PlatformDetector:
    """Detect and manage platform-specific operations."""

    def __init__(self):
        """Initialize platform detector."""
        self._platform = self._detect_platform()
        self._python_cmd = self._detect_python_command()

    def _detect_platform(self) -> str:
        """Detect the current platform."""
        if os.name == "nt":
            return "Windows"
        elif platform.system() == "Darwin":
            return "macOS"
        elif platform.system() == "Linux":
            return "Linux"
        else:
            return "Unknown"

    def get_platform_normalized(self) -> str:
        """Get normalized platform name for cross-platform compatibility."""
        system = platform.system().lower()
        if system == "darwin":
            return "macos"
        elif system == "linux":
            return "linux"
        elif system == "windows" or os.name == "nt":
            return "windows"
        else:
            return system

    def _detect_python_command(self) -> str:
        """Detect the best Python command to use."""
        # Priority: uv > conda/mamba > venv > system python
        if shutil.which("uv"):
            return "uv run python"

        # Check for conda environment
        conda_python = self.get_conda_python_path()
        if conda_python and Path(conda_python).exists():
            return str(conda_python)

        # Check for virtual environment
        venv_python = self.get_venv_python_path()
        if venv_python and Path(venv_python).exists():
            return str(venv_python)

        # Fall back to system python
        if self.is_windows():
            return "python"
        else:
            return "python3"

    @property
    def platform(self) -> str:
        """Get the current platform name."""
        return self._platform

    @property
    def python_cmd(self) -> str:
        """Get the Python command to use."""
        return self._python_cmd

    def is_windows(self) -> bool:
        """Check if running on Windows."""
        return self._platform == "Windows"

    def is_macos(self) -> bool:
        """Check if running on macOS."""
        return self._platform == "macOS"

    def is_linux(self) -> bool:
        """Check if running on Linux."""
        return self._platform == "Linux"

    def is_unix_like(self) -> bool:
        """Check if running on Unix-like system (macOS or Linux)."""
        return self.is_macos() or self.is_linux()

    def get_path_separator(self) -> str:
        """Get the path separator for the current platform."""
        return "\\" if self.is_windows() else "/"

    def get_null_device(self) -> str:
        """Get the null device path for the current platform."""
        return "nul" if self.is_windows() else "/dev/null"

    def get_venv_python_path(self) -> str | None:
        """Get the virtual environment Python path."""
        # Check VIRTUAL_ENV first, then local .venv
        venv_path = os.getenv("VIRTUAL_ENV")
        if venv_path:
            venv_dir = Path(venv_path)
        else:
            venv_dir = Path(".venv")
            if not venv_dir.exists():
                return None

        if self.is_windows():
            python_path = venv_dir / "Scripts" / "python.exe"
        else:
            python_path = venv_dir / "bin" / "python"

        return str(python_path) if python_path.exists() else None

    def get_venv_activate_path(self) -> str | None:
        """Get the virtual environment activation script path."""
        # Check VIRTUAL_ENV first, then local .venv
        venv_path = os.getenv("VIRTUAL_ENV")
        if venv_path:
            venv_dir = Path(venv_path)
        else:
            venv_dir = Path(".venv")
            if not venv_dir.exists():
                return None

        if self.is_windows():
            activate_path = venv_dir / "Scripts" / "activate"
        else:
            activate_path = venv_dir / "bin" / "activate"

        return str(activate_path) if activate_path.exists() else None

    def is_in_venv(self) -> bool:
        """Check if running in a virtual environment."""
        return (
            os.getenv("VIRTUAL_ENV") is not None
            or os.getenv("VENV") is not None
            or hasattr(sys, "real_prefix")
            or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
        )

    def is_in_conda_env(self) -> bool:
        """Check if running in a conda/mamba environment."""
        return (
            os.getenv("CONDA_DEFAULT_ENV") is not None
            or os.getenv("CONDA_PREFIX") is not None
            or os.getenv("MAMBA_DEFAULT_ENV") is not None
            or os.getenv("MAMBA_PREFIX") is not None
        )

    def get_conda_env_name(self) -> str | None:
        """Get the name of the current conda/mamba environment."""
        # Try conda first, then mamba
        env_name = os.getenv("CONDA_DEFAULT_ENV") or os.getenv("MAMBA_DEFAULT_ENV")
        return env_name if env_name and env_name != "base" else None

    def get_conda_prefix(self) -> Path | None:
        """Get the prefix path of the current conda/mamba environment."""
        prefix = os.getenv("CONDA_PREFIX") or os.getenv("MAMBA_PREFIX")
        return Path(prefix) if prefix else None

    def get_conda_python_path(self) -> str | None:
        """Get the conda/mamba environment Python path."""
        if not self.is_in_conda_env():
            return None

        conda_prefix = self.get_conda_prefix()
        if not conda_prefix or not conda_prefix.exists():
            return None

        if self.is_windows():
            python_path = conda_prefix / "python.exe"
        else:
            python_path = conda_prefix / "bin" / "python"

        return str(python_path) if python_path.exists() else None

    def get_conda_executable(self) -> str | None:
        """Get the conda or mamba executable to use."""
        # Prefer mamba if available (faster)
        if shutil.which("mamba"):
            return "mamba"
        elif shutil.which("conda"):
            return "conda"
        return None

    def is_conda_forge_available(self) -> bool:
        """Check if conda-forge channel is configured."""
        conda_exe = self.get_conda_executable()
        if not conda_exe:
            return False

        try:
            result = subprocess.run(
                [conda_exe, "config", "--show", "channels"], capture_output=True, text=True, timeout=10
            )
            return "conda-forge" in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False

    def run_command(self, cmd: str | list[str], shell: bool = False, **kwargs) -> subprocess.CompletedProcess:
        """Run a command with platform-appropriate settings.

        Args:
            cmd: Command to run - use list format for security, string only when shell=True
            shell: Whether to use shell (default: False for security)
            **kwargs: Additional arguments to pass to subprocess.run
        """
        return subprocess.run(cmd, shell=shell, **kwargs)

    def check_command_exists(self, command: str) -> bool:
        """Check if a command exists on the system."""
        return shutil.which(command) is not None

    def get_env_file_content(self, env_file: Path = Path(".env")) -> dict:
        """Read environment file content if it exists."""
        if not env_file.exists():
            return {}

        env_vars = {}
        try:
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()
        except Exception as e:
            logger.debug(f"Failed to read conda environment file {env_file}: {e}")

        return env_vars

    def install_uv(self) -> bool:
        """Install uv package manager for the current platform."""
        try:
            if self.is_windows():
                # Use PowerShell on Windows - download and execute separately for security
                import os
                import tempfile

                # Download script to temporary file first, then execute
                with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
                    # Download the install script
                    download_result = self.run_command(
                        ["powershell", "-Command", "Invoke-RestMethod https://astral.sh/uv/install.ps1"],
                        capture_output=True,
                        text=True,
                    )
                    if download_result.returncode != 0:
                        return False

                    f.write(download_result.stdout)
                    temp_script = f.name

                try:
                    # Execute the downloaded script
                    result = self.run_command(
                        ["powershell", "-ExecutionPolicy", "Bypass", "-File", temp_script],
                        capture_output=True,
                        text=True,
                    )
                    return result.returncode == 0
                finally:
                    # Clean up temporary script
                    try:
                        os.unlink(temp_script)
                    except OSError as e:
                        logger.debug(f"Failed to clean up temporary script {temp_script}: {e}")
            else:
                # Use curl and sh on Unix-like systems with secure argument list
                import os
                import tempfile

                # Download script to temporary file first, then execute
                with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
                    # Download the install script
                    download_result = self.run_command(
                        ["curl", "-LsSf", "https://astral.sh/uv/install.sh"], capture_output=True, text=True
                    )
                    if download_result.returncode != 0:
                        return False

                    f.write(download_result.stdout)
                    temp_script = f.name

                try:
                    # Make script executable and run it
                    os.chmod(temp_script, 0o755)
                    result = self.run_command(["sh", temp_script], capture_output=True, text=True)
                    return result.returncode == 0
                finally:
                    # Clean up temporary script
                    try:
                        os.unlink(temp_script)
                    except OSError as e:
                        logger.debug(f"Failed to clean up temporary script {temp_script}: {e}")

                return False
        except Exception as e:
            # Log uv installation failure for debugging platform issues
            logger.debug(f"Failed to install uv package manager: {e}")
            return False

    def remove_directory(self, path: Path) -> bool:
        """Remove a directory with platform-appropriate method."""
        try:
            if path.exists():
                shutil.rmtree(path)
                return True
            return False
        except Exception as e:
            # Log directory removal failure for debugging
            logger.debug(f"Failed to remove directory {path}: {e}")
            return False

    def copy_file(self, src: Path, dst: Path) -> bool:
        """Copy a file with error handling."""
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            # Log file copy failure for debugging
            logger.debug(f"Failed to copy file from {src} to {dst}: {e}")
            return False

    def make_executable(self, path: Path) -> bool:
        """Make a file executable (Unix-like systems only)."""
        if self.is_windows():
            return True  # Windows doesn't use Unix permissions

        try:
            import stat

            current_mode = path.stat().st_mode
            path.chmod(current_mode | stat.S_IEXEC)
            return True
        except Exception as e:
            # Log file permission change failure for debugging
            logger.debug(f"Failed to make file executable {path}: {e}")
            return False


# Global instance for easy access
platform_detector = PlatformDetector()


def get_platform() -> str:
    """Get the current platform name."""
    return platform_detector.platform


def get_platform_normalized() -> str:
    """Get normalized platform name for cross-platform compatibility."""
    return platform_detector.get_platform_normalized()


def get_python_command() -> str:
    """Get the Python command to use."""
    return platform_detector.python_cmd


def is_windows() -> bool:
    """Check if running on Windows."""
    return platform_detector.is_windows()


def is_unix_like() -> bool:
    """Check if running on Unix-like system."""
    return platform_detector.is_unix_like()


def run_platform_command(cmd: str | list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command with platform-appropriate settings."""
    return platform_detector.run_command(cmd, **kwargs)


def is_in_venv() -> bool:
    """Check if running in a virtual environment."""
    return platform_detector.is_in_venv()


def is_in_conda_env() -> bool:
    """Check if running in a conda/mamba environment."""
    return platform_detector.is_in_conda_env()


def get_conda_env_name() -> str | None:
    """Get the name of the current conda/mamba environment."""
    return platform_detector.get_conda_env_name()


def get_conda_python_path() -> str | None:
    """Get the conda/mamba environment Python path."""
    return platform_detector.get_conda_python_path()


def get_conda_executable() -> str | None:
    """Get the conda or mamba executable to use."""
    return platform_detector.get_conda_executable()


def safe_print(message: str, success_symbol: str = "✅", fallback_symbol: str = "[OK]") -> None:
    """Print a message with cross-platform compatible symbols.

    Args:
        message: The message to print
        success_symbol: Unicode symbol to use on capable terminals
        fallback_symbol: ASCII fallback symbol
    """
    import sys

    # Try to use Unicode symbols on capable terminals
    if hasattr(sys.stdout, "encoding") and sys.stdout.encoding:
        try:
            # Test if we can encode the success symbol
            success_symbol.encode(sys.stdout.encoding)
            print(f"{success_symbol} {message}")
        except (UnicodeEncodeError, LookupError):
            # Fall back to ASCII
            print(f"{fallback_symbol} {message}")
    else:
        # Default to ASCII fallback
        print(f"{fallback_symbol} {message}")


def safe_console_print(console, message: str, style: str | None = None, **kwargs) -> None:
    """Print a message using Rich console with cross-platform Unicode fallback.

    Args:
        console: Rich console instance
        message: The message to print
        style: Rich style to apply
        **kwargs: Additional arguments to pass to console.print
    """
    try:
        # Try Rich console first
        console.print(message, style=style, **kwargs)
    except UnicodeEncodeError:
        # Try without emoji/unicode characters
        ascii_message = _convert_to_ascii(message)
        try:
            console.print(ascii_message, style=style, **kwargs)
        except UnicodeEncodeError:
            # Final fallback to plain print
            print(ascii_message)


def _convert_to_ascii(message: str) -> str:
    """Convert Unicode emoji and symbols to ASCII equivalents.

    Args:
        message: The message to convert

    Returns:
        ASCII-safe version of the message
    """
    # Common emoji/symbol replacements
    replacements = {
        "🔍": "[SEARCH]",
        "📦": "[PACKAGE]",
        "✅": "[OK]",
        "❌": "[ERROR]",
        "⚠️": "[WARNING]",
        "📁": "[FOLDER]",
        "🐍": "[PYTHON]",
        "📊": "[STATS]",
        "🧪": "[TEST]",
        "🐳": "[DOCKER]",
        "🍺": "[HOMEBREW]",
        "🪣": "[SCOOP]",
        "🎉": "[SUCCESS]",
        "🔗": "[LINK]",
        "📥": "[DOWNLOAD]",
        "📄": "[PDF]",
        "🔒": "[SECURE]",
        "→": "->",
        "←": "<-",
        "↑": "^",
        "↓": "v",
        "⏭️": "[SKIP]",
        "⏯️": "[PAUSE]",
        "⏹️": "[STOP]",
        "🔧": "[CONFIG]",
        "🧹": "[CLEAN]",
        "📝": "[NOTE]",
        "🚀": "[LAUNCH]",
        "🔥": "[HOT]",
        "💡": "[IDEA]",
        "⭐": "[STAR]",
        "🎯": "[TARGET]",
        "🎪": "[CIRCUS]",
        "🎨": "[ART]",
        "🌟": "[STAR]",
        "💫": "[SPARKLE]",
        "🌈": "[RAINBOW]",
        "🎈": "[BALLOON]",
        "🎭": "[THEATRE]",
        "🔮": "[CRYSTAL]",
        "🪄": "[MAGIC]",
        "🎲": "[DICE]",
        # Add more as needed
    }

    ascii_message = message
    for emoji, replacement in replacements.items():
        ascii_message = ascii_message.replace(emoji, replacement)

    return ascii_message
