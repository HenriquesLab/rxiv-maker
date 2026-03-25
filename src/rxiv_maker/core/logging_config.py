"""Centralized logging configuration for rxiv-maker."""

import atexit
import logging
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

from ..utils.unicode_safe import convert_to_ascii, get_safe_icon


class _AsciiSafeFormatter(logging.Formatter):
    """Formatter that strips emoji/Rich markup for plain-text log files."""

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        # Strip Rich markup tags like [green], [/green], [red bold], etc.
        import re

        msg = re.sub(r"\[/?[a-z ]+\]", "", msg)
        # Convert emoji to ASCII equivalents
        msg = convert_to_ascii(msg)
        return msg


class RxivLogger:
    """Centralized logging configuration for rxiv-maker with Rich support."""

    _instance: Optional["RxivLogger"] = None
    _console: Console | None = None
    _log_file_path: Path | None = None
    _file_handler: logging.FileHandler | None = None

    def __new__(cls) -> "RxivLogger":
        """Create a new instance of the singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the singleton instance only once."""
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._console = Console()
        self._log_file_path: Path | None = None
        self._file_handler: logging.FileHandler | None = None
        self._setup_logger()

    def _setup_logger(self) -> None:
        """Setup the main logger with Rich handler."""
        # Create main logger
        self.logger = logging.getLogger("rxiv_maker")
        self.logger.setLevel(logging.INFO)  # Default level

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # Create Rich handler
        rich_handler = RichHandler(
            console=self._console,
            show_time=False,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
        )
        rich_handler.setFormatter(logging.Formatter("%(message)s"))

        self.logger.addHandler(rich_handler)

        # File handler will be added when log directory is set

    def set_log_directory(self, log_dir: Path) -> None:
        """Set the directory where log files should be created."""
        # Remove existing file handler if present
        if self._file_handler:
            self.logger.removeHandler(self._file_handler)
            self._file_handler.close()

        # Create log directory if it doesn't exist
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create new file handler with ASCII-safe formatter for Windows compatibility
        self._log_file_path = log_dir / "rxiv_maker.log"
        self._file_handler = logging.FileHandler(self._log_file_path, encoding="utf-8")
        self._file_handler.setLevel(logging.DEBUG)
        file_formatter = _AsciiSafeFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self._file_handler.setFormatter(file_formatter)
        self.logger.addHandler(self._file_handler)

    def get_log_file_path(self) -> Path | None:
        """Get the current log file path."""
        return self._log_file_path

    def set_level(self, level: str) -> None:
        """Set logging level."""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        if level.upper() in level_map:
            self.logger.setLevel(level_map[level.upper()])
            # Also update Rich handler level
            for handler in self.logger.handlers:
                if isinstance(handler, RichHandler):
                    handler.setLevel(level_map[level.upper()])

    def set_quiet(self, quiet: bool = True) -> None:
        """Enable/disable quiet mode (only errors and warnings)."""
        if quiet:
            self.set_level("WARNING")
        else:
            self.set_level("INFO")

    def debug(self, message: str) -> None:
        """Log debug message."""
        icon = get_safe_icon("🔧", "[DEBUG]")
        self.logger.debug(f"{icon} {message}")

    def info(self, message: str) -> None:
        """Log info message."""
        icon = get_safe_icon("ℹ️", "[INFO]")
        self.logger.info(f"{icon} {message}")

    def success(self, message: str) -> None:
        """Log success message."""
        icon = get_safe_icon("✅", "[OK]")
        self.logger.info(f"[green]{icon} {message}[/green]")

    def warning(self, message: str) -> None:
        """Log warning message."""
        icon = get_safe_icon("⚠️", "[WARNING]")
        self.logger.warning(f"[yellow]{icon} {message}[/yellow]")

    def error(self, message: str) -> None:
        """Log error message."""
        icon = get_safe_icon("❌", "[ERROR]")
        self.logger.error(f"[red]{icon} {message}[/red]")

    def critical(self, message: str) -> None:
        """Log critical message."""
        icon = get_safe_icon("💥", "[CRITICAL]")
        self.logger.critical(f"[red bold]{icon} {message}[/red bold]")

    def docker_info(self, message: str) -> None:
        """Log Docker-related info."""
        icon = get_safe_icon("🐳", "[DOCKER]")
        self.logger.info(f"[blue]{icon} {message}[/blue]")

    def tip(self, message: str) -> None:
        """Log helpful tip."""
        icon = get_safe_icon("💡", "[TIP]")
        self.logger.info(f"[yellow]{icon} {message}[/yellow]")

    @property
    def console(self) -> Console:
        """Get the Rich console instance."""
        if self._console is None:
            self._console = Console()
        return self._console

    def close_file_handler(self) -> None:
        """Close only the file handler, keeping console logging operational.

        This is needed on Windows before deleting the output directory,
        since open file handles prevent directory removal.
        """
        if self._file_handler:
            self.logger.removeHandler(self._file_handler)
            self._file_handler.close()
            self._file_handler = None
            self._log_file_path = None

    def cleanup(self) -> None:
        """Clean up resources, especially file handlers for Windows compatibility."""
        if self._file_handler:
            self.logger.removeHandler(self._file_handler)
            self._file_handler.close()
            self._file_handler = None

        # Also close any other handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            if hasattr(handler, "close"):
                handler.close()


# Global logger instance
_logger_instance = RxivLogger()

# Register automatic cleanup on exit for Windows compatibility
atexit.register(_logger_instance.cleanup)


# Convenience functions
def get_logger() -> RxivLogger:
    """Get the global logger instance."""
    return _logger_instance


def debug(message: str) -> None:
    """Log debug message."""
    _logger_instance.debug(message)


def info(message: str) -> None:
    """Log info message."""
    _logger_instance.info(message)


def success(message: str) -> None:
    """Log success message."""
    _logger_instance.success(message)


def warning(message: str) -> None:
    """Log warning message."""
    _logger_instance.warning(message)


def error(message: str) -> None:
    """Log error message."""
    _logger_instance.error(message)


def critical(message: str) -> None:
    """Log critical message."""
    _logger_instance.critical(message)


def docker_info(message: str) -> None:
    """Log Docker-related info."""
    _logger_instance.docker_info(message)


def tip(message: str) -> None:
    """Log helpful tip."""
    _logger_instance.tip(message)


def set_quiet(quiet: bool = True) -> None:
    """Enable/disable quiet mode."""
    _logger_instance.set_quiet(quiet)


def set_debug(debug_mode: bool = True) -> None:
    """Enable/disable debug mode."""
    if debug_mode:
        _logger_instance.set_level("DEBUG")
    else:
        _logger_instance.set_level("INFO")


def set_log_directory(log_dir: Path) -> None:
    """Set the directory where log files should be created."""
    _logger_instance.set_log_directory(log_dir)


def get_log_file_path() -> Path | None:
    """Get the current log file path."""
    return _logger_instance.get_log_file_path()


def close_file_handler() -> None:
    """Close only the file handler, keeping console logging operational."""
    _logger_instance.close_file_handler()


def cleanup() -> None:
    """Clean up logging resources."""
    _logger_instance.cleanup()
